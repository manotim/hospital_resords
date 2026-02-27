# /home/devmike/dev/hosi/hospital_records_system/hospital_records/apps/reports/views.py
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail
from django.conf import settings
import json
from .report_generators import (
    stream_csv_response,
    generate_medical_records_csv,
    generate_diagnosis_frequency_csv,
    generate_prescription_analysis_csv,
    generate_lab_utilization_csv,
    generate_imaging_utilization_csv,
    generate_procedure_analysis_csv,
    generate_patient_visit_summary_csv
)
import csv
import xlwt
from datetime import datetime, timedelta
from django.utils import timezone
from weasyprint import HTML
import tempfile

from hospital_records.apps.patients.models import Patient, VitalSign
from hospital_records.apps.records.models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)
from .models import ReportTemplate, GeneratedReport, ScheduledReport, DashboardWidget
from .forms import (
    DateRangeForm, ReportGenerationForm, PatientCensusForm,
    DiagnosisFrequencyForm, PrescriptionAnalysisForm, LabUtilizationForm,
    ScheduledReportForm, DashboardWidgetForm
)

logger = logging.getLogger(__name__)

@login_required
def report_dashboard(request):
    """Main reports dashboard"""
    recent_reports = GeneratedReport.objects.filter(
        generated_by=request.user
    ).order_by('-generated_at')[:10]
    
    scheduled_reports = ScheduledReport.objects.filter(
        created_by=request.user,
        is_active=True
    )
    
    # Get dashboard widgets
    widgets = DashboardWidget.objects.filter(is_active=True)
    
    # Generate widget data
    widget_data = []
    for widget in widgets:
        data = generate_widget_data(widget)
        widget_data.append({
            'widget': widget,
            'data': data
        })
    
    context = {
        'recent_reports': recent_reports,
        'scheduled_reports': scheduled_reports,
        'widgets': widget_data,
        'report_categories': ReportTemplate.REPORT_CATEGORIES,
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def generate_report(request):
    """Generate a new report"""
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            report_type = form.cleaned_data['report_type']
            title = form.cleaned_data['title']
            report_format = form.cleaned_data['format']
            
            # Get date range
            start_date, end_date = get_date_range(date_form)
            
            # Generate report data based on type
            report_data = {}
            
            if report_type == 'patient_census':
                report_data = generate_patient_census(start_date, end_date, request.POST)
            elif report_type == 'medical_records':
                report_data = generate_medical_records_summary(start_date, end_date)
            elif report_type == 'diagnosis_frequency':
                report_data = generate_diagnosis_frequency(start_date, end_date, request.POST)
            elif report_type == 'prescription_analysis':
                report_data = generate_prescription_analysis(start_date, end_date, request.POST)
            elif report_type == 'lab_utilization':
                report_data = generate_lab_utilization(start_date, end_date, request.POST)
            elif report_type == 'imaging_utilization':
                report_data = generate_imaging_utilization(start_date, end_date)
            elif report_type == 'patient_demographics':
                report_data = generate_patient_demographics(start_date, end_date)
            elif report_type == 'physician_workload':
                report_data = generate_physician_workload(start_date, end_date)
            elif report_type == 'procedure_analysis':
                report_data = generate_procedure_analysis(start_date, end_date)
            
            # Create report record
            report = GeneratedReport.objects.create(
                title=title,
                report_type=report_type,
                format=report_format,
                start_date=start_date,
                end_date=end_date,
                parameters=form.cleaned_data,
                report_data=report_data,
                status='completed',
                generated_by=request.user,
                completed_at=timezone.now()
            )
            
            # Generate file based on format
            if report_format == 'pdf':
                generate_pdf_report(report)
            elif report_format == 'excel':
                generate_excel_report(report)
            elif report_format == 'csv':
                generate_csv_report(report)
            
            messages.success(request, f'Report "{title}" generated successfully!')
            return redirect('reports:view_report', pk=report.pk)
    else:
        form = ReportGenerationForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
    }
    return render(request, 'reports/generate_report.html', context)

@login_required
def view_report(request, pk):
    """View a generated report"""
    report = get_object_or_404(GeneratedReport, pk=pk)
    
    # Ensure user has permission to view this report
    if report.generated_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this report.')
        return redirect('reports:dashboard')
    
    context = {
        'report': report,
    }
    return render(request, 'reports/view_report.html', context)

@login_required
def download_report(request, pk):
    """Download a generated report file"""
    report = get_object_or_404(GeneratedReport, pk=pk)
    
    if not report.report_file:
        messages.error(request, 'Report file not found.')
        return redirect('reports:view_report', pk=report.pk)
    
    response = HttpResponse(report.report_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{report.report_file.name}"'
    return response

@login_required
def scheduled_reports(request):
    """Manage scheduled reports"""
    schedules = ScheduledReport.objects.filter(created_by=request.user)
    
    context = {
        'schedules': schedules,
    }
    return render(request, 'reports/scheduled_reports.html', context)

@login_required
def create_schedule(request):
    """Create a new scheduled report"""
    if request.method == 'POST':
        form = ScheduledReportForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            
            # Parse email recipients
            if isinstance(schedule.email_recipients, str):
                schedule.email_recipients = [
                    email.strip() for email in schedule.email_recipients.split(',') 
                    if email.strip()
                ]
            
            schedule.save()
            messages.success(request, 'Report schedule created successfully!')
            return redirect('reports:scheduled_reports')
    else:
        form = ScheduledReportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'reports/schedule_form.html', context)

@login_required
def edit_schedule(request, pk):
    """Edit a scheduled report"""
    schedule = get_object_or_404(ScheduledReport, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = ScheduledReportForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save(commit=False)
            if isinstance(schedule.email_recipients, str):
                schedule.email_recipients = [
                    email.strip() for email in schedule.email_recipients.split(',') 
                    if email.strip()
                ]
            schedule.save()
            messages.success(request, 'Schedule updated successfully!')
            return redirect('reports:scheduled_reports')
    else:
        # Convert email list to string for display
        initial_data = {
            'email_recipients': ', '.join(schedule.email_recipients) if schedule.email_recipients else ''
        }
        form = ScheduledReportForm(instance=schedule, initial=initial_data)
    
    context = {
        'form': form,
        'schedule': schedule,
    }
    return render(request, 'reports/schedule_form.html', context)

@login_required
def delete_schedule(request, pk):
    """Delete a scheduled report"""
    schedule = get_object_or_404(ScheduledReport, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully!')
        return redirect('reports:scheduled_reports')
    
    context = {
        'schedule': schedule,
    }
    return render(request, 'reports/schedule_confirm_delete.html', context)

@login_required
@ensure_csrf_cookie
def patient_census_report(request):
    """Generate patient census report as CSV download"""
    logger.info(f"Patient census report request method: {request.method}")
    
    if request.method == 'POST':
        logger.info("Processing POST request")
        logger.info(f"POST data: {request.POST}")
        
        form = PatientCensusForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        logger.info(f"Form valid: {form.is_valid()}")
        logger.info(f"Date form valid: {date_form.is_valid()}")
        
        if form.is_valid() and date_form.is_valid():
            try:
                start_date, end_date = get_date_range(date_form)
                logger.info(f"Date range: {start_date} to {end_date}")
                
                census_type = form.cleaned_data['census_type']
                group_by = form.cleaned_data['group_by']
                logger.info(f"Census type: {census_type}, Group by: {group_by}")
                
                # Create CSV response
                response = HttpResponse(content_type='text/csv')
                filename = f"patient_census_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                writer = csv.writer(response)
                
                # Write headers based on group_by
                if group_by == 'status':
                    writer.writerow(['Patient Status', 'Count', 'Percentage'])
                elif group_by == 'gender':
                    writer.writerow(['Gender', 'Count', 'Percentage'])
                elif group_by == 'age_group':
                    writer.writerow(['Age Group', 'Count', 'Percentage'])
                else:  # daily registration
                    writer.writerow(['Date', 'New Patients', 'Total Patients', 'Active Patients'])
                
                # Get total patients for percentage calculations
                total_patients = Patient.objects.filter(
                    registration_date__range=[start_date, end_date]
                ).count()
                logger.info(f"Total patients in range: {total_patients}")
                
                if group_by == 'status':
                    # Group by patient status
                    status_counts = Patient.objects.filter(
                        registration_date__range=[start_date, end_date]
                    ).values('status').annotate(
                        count=Count('id')
                    ).order_by('-count')
                    
                    for item in status_counts:
                        status = item['status'] or 'Unknown'
                        count = item['count']
                        percentage = (count / total_patients * 100) if total_patients > 0 else 0
                        writer.writerow([status, count, f"{percentage:.1f}%"])
                        
                elif group_by == 'gender':
                    # Group by gender
                    gender_counts = Patient.objects.filter(
                        registration_date__range=[start_date, end_date]
                    ).values('gender').annotate(
                        count=Count('id')
                    ).order_by('-count')
                    
                    for item in gender_counts:
                        gender = item['gender'] or 'Unknown'
                        count = item['count']
                        percentage = (count / total_patients * 100) if total_patients > 0 else 0
                        writer.writerow([gender, count, f"{percentage:.1f}%"])
                        
                elif group_by == 'age_group':
                    # Calculate age groups
                    age_groups = {
                        '0-18': 0,
                        '19-35': 0,
                        '36-50': 0,
                        '51-65': 0,
                        '65+': 0,
                    }
                    
                    patients = Patient.objects.filter(
                        registration_date__range=[start_date, end_date]
                    ).iterator()
                    
                    for patient in patients:
                        age = patient.age()
                        if age <= 18:
                            age_groups['0-18'] += 1
                        elif age <= 35:
                            age_groups['19-35'] += 1
                        elif age <= 50:
                            age_groups['36-50'] += 1
                        elif age <= 65:
                            age_groups['51-65'] += 1
                        else:
                            age_groups['65+'] += 1
                    
                    for group, count in age_groups.items():
                        percentage = (count / total_patients * 100) if total_patients > 0 else 0
                        writer.writerow([group, count, f"{percentage:.1f}%"])
                
                else:  # daily trend
                    # Get daily registration counts
                    daily_stats = Patient.objects.filter(
                        registration_date__range=[start_date, end_date]
                    ).annotate(
                        date=TruncDate('registration_date')
                    ).values('date').annotate(
                        new_patients=Count('id')
                    ).order_by('date')
                    
                    running_total = 0
                    for stat in daily_stats.iterator():
                        date = stat['date']
                        new_patients = stat['new_patients']
                        running_total += new_patients
                        
                        # Get active patients on this date (simplified)
                        active_patients = Patient.objects.filter(
                            registration_date__lte=date + timedelta(days=1),
                            status='active'
                        ).count()
                        
                        writer.writerow([
                            date.strftime('%Y-%m-%d'),
                            new_patients,
                            running_total,
                            active_patients
                        ])
                
                logger.info("CSV generated successfully, returning response")
                return response
                
            except Exception as e:
                logger.error(f"Error generating report: {str(e)}", exc_info=True)
                return HttpResponse(f"Error generating report: {str(e)}", status=500)
        else:
            logger.error(f"Form errors: {form.errors}, Date form errors: {date_form.errors}")
            return HttpResponse("Form validation failed", status=400)
    
    else:
        form = PatientCensusForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
        'title': 'Patient Census Report',
    }
    return render(request, 'reports/report_form.html', context)

    
@login_required
def medical_records_report(request):
    """Generate medical records report"""
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            filename = f"medical_records_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Write headers
            writer.writerow([
                'Record #', 'Patient Name', 'Patient ID', 'Doctor', 
                'Record Type', 'Visit Date', 'Chief Complaint', 
                'Assessment', 'Follow-up Date', 'Status'
            ])
            
            # Get medical records
            records = MedicalRecord.objects.filter(
                visit_date__range=[start_date, end_date]
            ).select_related('patient', 'doctor').iterator()
            
            for record in records:
                writer.writerow([
                    record.record_number,
                    record.patient.get_full_name() if record.patient else 'Unknown',
                    record.patient.id if record.patient else 'N/A',
                    record.doctor.get_full_name() if record.doctor else 'Not assigned',
                    record.get_record_type_display(),
                    record.visit_date.strftime('%Y-%m-%d %H:%M'),
                    record.chief_complaint[:100] + '...' if len(record.chief_complaint) > 100 else record.chief_complaint,
                    record.assessment[:100] + '...' if len(record.assessment) > 100 else record.assessment,
                    record.follow_up_date.strftime('%Y-%m-%d') if record.follow_up_date else 'None',
                    'Active' if record.is_active else 'Inactive'
                ])
            
            return response
    
    else:
        form = MedicalRecordForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
        'title': 'Medical Records Report',
    }
    return render(request, 'reports/report_form.html', context)

@login_required
def diagnosis_frequency_report(request):
    """Generate diagnosis frequency report as CSV download"""
    if request.method == 'POST':
        form = DiagnosisFrequencyForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            scope = form.cleaned_data.get('scope', 'all')
            min_occurrences = int(form.cleaned_data.get('min_occurrences', 1))
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            filename = f"diagnosis_frequency_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Write headers
            writer.writerow(['ICD-10 Code', 'Description', 'Count', 'Primary Diagnoses', 'Status Distribution'])
            
            # Get diagnoses
            diagnoses = Diagnosis.objects.filter(
                medical_record__visit_date__range=[start_date, end_date]
            )
            
            if scope == 'primary':
                diagnoses = diagnoses.filter(is_primary=True)
            
            # Group by diagnosis
            freq = diagnoses.values('icd10_code', 'description').annotate(
                total_count=Count('id'),
                primary_count=Count('id', filter=Q(is_primary=True)),
                active_count=Count('id', filter=Q(status='active')),
                resolved_count=Count('id', filter=Q(status='resolved')),
                chronic_count=Count('id', filter=Q(status='chronic'))
            ).order_by('-total_count')
            
            if scope in ['top_10', 'top_20']:
                limit = 10 if scope == 'top_10' else 20
                freq = freq[:limit]
            else:
                freq = freq.filter(total_count__gte=min_occurrences)
            
            for item in freq.iterator():
                status_dist = f"Active: {item['active_count']}, Resolved: {item['resolved_count']}, Chronic: {item['chronic_count']}"
                writer.writerow([
                    item['icd10_code'],
                    item['description'][:100],
                    item['total_count'],
                    item['primary_count'],
                    status_dist
                ])
            
            return response
    
    else:
        form = DiagnosisFrequencyForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
        'title': 'Diagnosis Frequency Report',
    }
    return render(request, 'reports/report_form.html', context)

@login_required
def prescription_analysis_report(request):
    """Generate prescription analysis report as CSV download"""
    if request.method == 'POST':
        form = PrescriptionAnalysisForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            analysis_type = form.cleaned_data.get('analysis_type', 'most_prescribed')
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            filename = f"prescription_analysis_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Write report info
            writer.writerow(['Prescription Analysis Report'])
            writer.writerow([f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            # Get prescriptions
            prescriptions = Prescription.objects.filter(
                prescribed_date__range=[start_date, end_date]
            )
            
            if analysis_type == 'most_prescribed':
                writer.writerow(['Medication Name', 'Times Prescribed', 'Average Dosage', 'Total Quantity'])
                
                med_counts = prescriptions.values('medication_name').annotate(
                    count=Count('id'),
                    avg_dosage=Avg('dosage'),
                    total_quantity=Sum('quantity')
                ).order_by('-count')[:100]
                
                for item in med_counts.iterator():
                    writer.writerow([
                        item['medication_name'] or 'Unknown',
                        item['count'],
                        f"{item['avg_dosage']:.1f}" if item['avg_dosage'] else 'N/A',
                        item['total_quantity'] or 0
                    ])
            
            elif analysis_type == 'by_frequency':
                writer.writerow(['Frequency', 'Prescription Count', 'Average Dosage'])
                
                freq_counts = prescriptions.values('frequency').annotate(
                    count=Count('id'),
                    avg_dosage=Avg('dosage')
                ).order_by('-count')
                
                for item in freq_counts.iterator():
                    writer.writerow([
                        item['frequency'] or 'Not specified',
                        item['count'],
                        f"{item['avg_dosage']:.1f}" if item['avg_dosage'] else 'N/A'
                    ])
            
            return response
    
    else:
        form = PrescriptionAnalysisForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
        'title': 'Prescription Analysis Report',
    }
    return render(request, 'reports/report_form.html', context)

@login_required
def lab_utilization_report(request):
    """Generate lab utilization report as CSV download"""
    if request.method == 'POST':
        form = LabUtilizationForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            scope = form.cleaned_data.get('scope', 'tests_ordered')
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            filename = f"lab_utilization_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Write report info
            writer.writerow(['Lab Utilization Report'])
            writer.writerow([f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            lab_orders = LabOrder.objects.filter(
                ordered_date__range=[start_date, end_date]
            )
            
            if scope == 'tests_ordered':
                writer.writerow(['Test Name', 'Test Code', 'Times Ordered', 'Completed', 'Pending', 'Cancelled'])
                
                test_stats = lab_orders.values('test_name', 'test_code').annotate(
                    total=Count('id'),
                    completed=Count('id', filter=Q(status='completed')),
                    pending=Count('id', filter=Q(status__in=['ordered', 'collected', 'in_progress'])),
                    cancelled=Count('id', filter=Q(status='cancelled'))
                ).order_by('-total')[:100]
                
                for item in test_stats.iterator():
                    writer.writerow([
                        item['test_name'] or 'Unknown',
                        item['test_code'] or 'N/A',
                        item['total'],
                        item['completed'],
                        item['pending'],
                        item['cancelled']
                    ])
            
            elif scope == 'abnormal_results':
                writer.writerow(['Test Name', 'Patient', 'Result Value', 'Reference Range', 'Unit', 'Performed Date'])
                
                abnormal = LabResult.objects.filter(
                    lab_order__ordered_date__range=[start_date, end_date],
                    is_abnormal=True
                ).select_related('lab_order', 'lab_order__medical_record__patient').order_by('-performed_date')
                
                for result in abnormal.iterator():
                    patient = result.lab_order.medical_record.patient if result.lab_order.medical_record else None
                    writer.writerow([
                        result.lab_order.test_name,
                        patient.get_full_name() if patient else 'Unknown',
                        result.result_value,
                        result.reference_range,
                        result.unit,
                        result.performed_date.strftime('%Y-%m-%d %H:%M') if result.performed_date else 'N/A'
                    ])
            
            return response
    
    else:
        form = LabUtilizationForm()
        date_form = DateRangeForm()
    
    context = {
        'form': form,
        'date_form': date_form,
        'title': 'Lab Utilization Report',
    }
    return render(request, 'reports/report_form.html', context)

# Helper functions for generating report data

def get_date_range(date_form):
    """Extract date range from form"""
    date_range = date_form.cleaned_data['date_range']
    today = timezone.now().date()  # This uses the imported timezone at the top
    
    if date_range == 'today':
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday, datetime.max.time())
    elif date_range == 'this_week':
        start_date = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif date_range == 'last_week':
        last_week = today - timedelta(weeks=1)
        start_date = datetime.combine(last_week - timedelta(days=last_week.weekday()), datetime.min.time())
        end_date = datetime.combine(last_week + timedelta(days=6 - last_week.weekday()), datetime.max.time())
    elif date_range == 'this_month':
        start_date = datetime.combine(today.replace(day=1), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif date_range == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        start_date = datetime.combine(last_month.replace(day=1), datetime.min.time())
        end_date = datetime.combine(last_month, datetime.max.time())
    elif date_range == 'this_quarter':
        quarter = (today.month - 1) // 3
        start_date = datetime.combine(today.replace(month=quarter*3+1, day=1), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif date_range == 'last_quarter':
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start_date = datetime.combine(today.replace(year=today.year-1, month=10, day=1), datetime.min.time())
            end_date = datetime.combine(today.replace(year=today.year-1, month=12, day=31), datetime.max.time())
        else:
            start_date = datetime.combine(today.replace(month=quarter*3-2, day=1), datetime.min.time())
            end_date = datetime.combine(today.replace(month=quarter*3, day=1) - timedelta(days=1), datetime.max.time())
    elif date_range == 'this_year':
        start_date = datetime.combine(today.replace(month=1, day=1), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif date_range == 'last_year':
        start_date = datetime.combine(today.replace(year=today.year-1, month=1, day=1), datetime.min.time())
        end_date = datetime.combine(today.replace(year=today.year-1, month=12, day=31), datetime.max.time())
    else:  # custom
        start_date = datetime.combine(date_form.cleaned_data['start_date'], datetime.min.time())
        end_date = datetime.combine(date_form.cleaned_data['end_date'], datetime.max.time())
    
    # Make timezone aware - remove the duplicate import
    start_date = timezone.make_aware(start_date)
    end_date = timezone.make_aware(end_date)
    
    return start_date, end_date



def generate_patient_census(start_date, end_date, params):
    """Generate patient census data for display"""
    data = {
        'total_patients': Patient.objects.filter(
            registration_date__range=[start_date, end_date]
        ).count(),
        'active_patients': Patient.objects.filter(
            status='active'
        ).count(),
        'by_gender': [],
        'by_status': [],
    }
    
    # Group by gender
    gender_counts = Patient.objects.filter(
        registration_date__range=[start_date, end_date]
    ).values('gender').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for item in gender_counts:
        data['by_gender'].append({
            'gender': item['gender'] or 'Unknown',
            'count': item['count']
        })
    
    # Group by status
    status_counts = Patient.objects.filter(
        registration_date__range=[start_date, end_date]
    ).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for item in status_counts:
        data['by_status'].append({
            'status': item['status'] or 'Unknown',
            'count': item['count']
        })
    
    return data

def generate_medical_records_summary(start_date, end_date):
    """Generate medical records summary"""
    records = MedicalRecord.objects.filter(
        visit_date__range=[start_date, end_date]
    )
    
    data = {
        'total_records': records.count(),
        'by_type': [],
        'by_doctor': [],
        'daily_trend': [],
    }
    
    # Group by record type
    type_counts = records.values('record_type').annotate(
        count=Count('id')
    )
    
    for item in type_counts:
        data['by_type'].append({
            'type': item['record_type'],
            'count': item['count']
        })
    
    # Group by doctor
    doctor_counts = records.values('doctor__first_name', 'doctor__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for item in doctor_counts:
        doctor_name = f"{item['doctor__first_name'] or ''} {item['doctor__last_name'] or ''}".strip()
        data['by_doctor'].append({
            'doctor': doctor_name or 'Unknown',
            'count': item['count']
        })
    
    # Daily trend
    daily = records.annotate(
        date=TruncDate('visit_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    for item in daily:
        data['daily_trend'].append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        })
    
    return data

def generate_procedure_analysis(start_date, end_date):
    """Generate procedure analysis data"""
    procedures = Procedure.objects.filter(
        date_performed__range=[start_date, end_date]
    )
    
    data = {
        'total_procedures': procedures.count(),
        'by_type': [],
        'by_doctor': [],
    }
    
    # Group by procedure name
    proc_counts = procedures.values('procedure_name').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    for item in proc_counts:
        data['by_type'].append({
            'name': item['procedure_name'],
            'count': item['count']
        })
    
    # Group by doctor
    doctor_counts = procedures.values('performed_by__first_name', 'performed_by__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for item in doctor_counts:
        doctor_name = f"{item['performed_by__first_name'] or ''} {item['performed_by__last_name'] or ''}".strip()
        data['by_doctor'].append({
            'doctor': doctor_name or 'Unknown',
            'count': item['count']
        })
    
    return data

def generate_physician_workload(start_date, end_date):
    """Generate physician workload report"""
    from django.contrib.auth.models import User
    
    data = {
        'physicians': [],
    }
    
    # Get all doctors (users with medical records)
    doctors = User.objects.filter(
        medical_records__visit_date__range=[start_date, end_date]
    ).distinct()
    
    for doctor in doctors:
        records = MedicalRecord.objects.filter(
            doctor=doctor,
            visit_date__range=[start_date, end_date]
        )
        
        prescriptions = Prescription.objects.filter(
            medical_record__doctor=doctor,
            prescribed_date__range=[start_date, end_date]
        )
        
        lab_orders = LabOrder.objects.filter(
            ordered_by=doctor,
            ordered_date__range=[start_date, end_date]
        )
        
        data['physicians'].append({
            'name': doctor.get_full_name() or doctor.username,
            'patient_count': records.values('patient').distinct().count(),
            'record_count': records.count(),
            'prescription_count': prescriptions.count(),
            'lab_orders': lab_orders.count(),
        })
    
    # Sort by patient count
    data['physicians'].sort(key=lambda x: x['patient_count'], reverse=True)
    
    return data

def generate_widget_data(widget):
    """Generate data for dashboard widget"""
    end_date = timezone.now()
    
    if widget.refresh_interval > 0:
        start_date = end_date - timedelta(minutes=widget.refresh_interval)
    else:
        start_date = end_date - timedelta(days=30)  # Default to 30 days
    
    if widget.report_type == 'patient_census':
        return generate_patient_census(start_date, end_date, {})
    elif widget.report_type == 'medical_records':
        return generate_medical_records_summary(start_date, end_date)
    elif widget.report_type == 'diagnosis_frequency':
        return generate_diagnosis_frequency(start_date, end_date, {'scope': 'top_10'})
    elif widget.report_type == 'lab_utilization':
        return generate_lab_utilization(start_date, end_date, {})
    else:
        return {}

def generate_pdf_report(report):
    """Generate PDF file for report"""
    try:
        html_string = render_to_string('reports/pdf_template.html', {'report': report})
        html = HTML(string=html_string)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            html.write_pdf(target=tmp_file.name)
            tmp_file.seek(0)
            
            from django.core.files import File
            with open(tmp_file.name, 'rb') as f:
                report.report_file.save(
                    f"report_{report.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    File(f)
                )
    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()

def generate_excel_report(report):
    """Generate Excel file for report"""
    try:
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Report')
        
        # Add title
        sheet.write(0, 0, report.title)
        
        # Add date range
        sheet.write(1, 0, f"Period: {report.start_date.strftime('%Y-%m-%d')} to {report.end_date.strftime('%Y-%m-%d')}")
        
        # Add data (simplified - you'd need to customize based on report type)
        row = 3
        for key, value in report.report_data.items():
            if isinstance(value, list):
                sheet.write(row, 0, key)
                row += 1
                for item in value:
                    col = 0
                    for k, v in item.items():
                        sheet.write(row, col, f"{k}: {v}")
                        col += 1
                    row += 1
            else:
                sheet.write(row, 0, f"{key}: {value}")
                row += 1
        
        with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as tmp_file:
            workbook.save(tmp_file.name)
            tmp_file.seek(0)
            
            from django.core.files import File
            with open(tmp_file.name, 'rb') as f:
                report.report_file.save(
                    f"report_{report.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xls",
                    File(f)
                )
    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()

def generate_csv_report(report):
    """Generate CSV file for report"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp_file:
            writer = csv.writer(tmp_file)
            
            # Write title
            writer.writerow([report.title])
            writer.writerow([f"Period: {report.start_date.strftime('%Y-%m-%d')} to {report.end_date.strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            # Write data (simplified)
            for key, value in report.report_data.items():
                if isinstance(value, list):
                    writer.writerow([key])
                    for item in value:
                        row = []
                        for k, v in item.items():
                            row.append(f"{k}: {v}")
                        writer.writerow(row)
                    writer.writerow([])
                else:
                    writer.writerow([f"{key}: {value}"])
            
            tmp_file.flush()
            
            from django.core.files import File
            with open(tmp_file.name, 'rb') as f:
                report.report_file.save(
                    f"report_{report.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    File(f)
                )
    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()

# API endpoints for AJAX calls

@login_required
def api_report_data(request, report_type):
    """API endpoint to get report data for charts"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date)
        end_date = timezone.make_aware(end_date)
    else:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    
    if report_type == 'patient_census':
        data = generate_patient_census(start_date, end_date, request.GET)
    elif report_type == 'medical_records':
        data = generate_medical_records_summary(start_date, end_date)
    elif report_type == 'diagnosis_frequency':
        data = generate_diagnosis_frequency(start_date, end_date, request.GET)
    elif report_type == 'prescription_analysis':
        data = generate_prescription_analysis(start_date, end_date, request.GET)
    elif report_type == 'lab_utilization':
        data = generate_lab_utilization(start_date, end_date, request.GET)
    else:
        data = {}
    
    return JsonResponse(data)

@login_required
def api_save_widget(request):
    """API endpoint to save dashboard widget configuration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            widget = DashboardWidget.objects.create(
                name=data['name'],
                widget_type=data['widget_type'],
                chart_type=data.get('chart_type'),
                report_type=data['report_type'],
                data_config=data.get('data_config', {}),
                width=data.get('width', 6),
                height=data.get('height', 300),
                refresh_interval=data.get('refresh_interval', 0)
            )
            return JsonResponse({'success': True, 'widget_id': widget.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Download views using report_generators
@login_required
def medical_records_report_download(request):
    """Generate medical records report as CSV download using generator"""
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"medical_records_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_medical_records_csv,
                filename,
                start_date,
                end_date,
                request.POST
            )
    
    return redirect('reports:medical_records')

@login_required
def diagnosis_frequency_report_download(request):
    """Generate diagnosis frequency report as CSV download using generator"""
    if request.method == 'POST':
        form = DiagnosisFrequencyForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"diagnosis_frequency_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_diagnosis_frequency_csv,
                filename,
                start_date,
                end_date,
                request.POST
            )
    
    return redirect('reports:diagnosis_frequency')

@login_required
def prescription_analysis_report_download(request):
    """Generate prescription analysis report as CSV download using generator"""
    if request.method == 'POST':
        form = PrescriptionAnalysisForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"prescription_analysis_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_prescription_analysis_csv,
                filename,
                start_date,
                end_date,
                request.POST
            )
    
    return redirect('reports:prescription_analysis')

@login_required
def lab_utilization_report_download(request):
    """Generate lab utilization report as CSV download using generator"""
    if request.method == 'POST':
        form = LabUtilizationForm(request.POST)
        date_form = DateRangeForm(request.POST)
        
        if form.is_valid() and date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"lab_utilization_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_lab_utilization_csv,
                filename,
                start_date,
                end_date,
                request.POST
            )
    
    return redirect('reports:lab_utilization')

@login_required
def imaging_utilization_report_download(request):
    """Generate imaging utilization report as CSV download using generator"""
    if request.method == 'POST':
        date_form = DateRangeForm(request.POST)
        
        if date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"imaging_utilization_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_imaging_utilization_csv,
                filename,
                start_date,
                end_date
            )
    
    return redirect('reports:imaging_utilization')

@login_required
def procedure_analysis_report_download(request):
    """Generate procedure analysis report as CSV download using generator"""
    if request.method == 'POST':
        date_form = DateRangeForm(request.POST)
        
        if date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"procedure_analysis_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_procedure_analysis_csv,
                filename,
                start_date,
                end_date
            )
    
    return redirect('reports:procedure_analysis')

@login_required
def patient_visit_summary_report_download(request):
    """Generate patient visit summary report as CSV download using generator"""
    if request.method == 'POST':
        date_form = DateRangeForm(request.POST)
        
        if date_form.is_valid():
            start_date, end_date = get_date_range(date_form)
            
            filename = f"patient_visits_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return stream_csv_response(
                generate_patient_visit_summary_csv,
                filename,
                start_date,
                end_date
            )
    
    return redirect('reports:patient_visit_summary')