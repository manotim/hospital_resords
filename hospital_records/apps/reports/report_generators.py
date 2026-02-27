# /home/devmike/dev/hosi/hospital_records_system/hospital_records/apps/reports/report_generators.py

import csv
import logging
from datetime import datetime, timedelta
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate, TruncMonth

from hospital_records.apps.patients.models import Patient
from hospital_records.apps.records.models import (
    MedicalRecord,
    Diagnosis,
    Prescription,
    LabOrder,
    LabResult,
    ImagingOrder,
    ImagingResult,
    Procedure,
    ClinicalNote
)

logger = logging.getLogger(__name__)

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value

def stream_csv_response(generator_func, filename, *args, **kwargs):
    """Create a streaming CSV response"""
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in generator_func(*args, **kwargs)),
        content_type="text/csv"
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def generate_medical_records_csv(start_date, end_date, params):
    """Generator for medical records report CSV"""
    yield ['Record #', 'Patient Name', 'Patient ID', 'Doctor', 'Record Type', 'Visit Date', 
           'Chief Complaint', 'Assessment', 'Follow-up Date', 'Status']
    
    records = MedicalRecord.objects.filter(
        visit_date__range=[start_date, end_date]
    ).select_related('patient', 'doctor').only(
        'record_number', 'patient__first_name', 'patient__last_name', 'patient__id',
        'doctor__first_name', 'doctor__last_name', 'record_type', 'visit_date',
        'chief_complaint', 'assessment', 'follow_up_date', 'is_active'
    ).iterator()
    
    for record in records:
        yield [
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
        ]

def generate_diagnosis_frequency_csv(start_date, end_date, params):
    """Generator for diagnosis frequency CSV"""
    scope = params.get('scope', 'all')
    min_occurrences = int(params.get('min_occurrences', 1))
    
    # Yield header
    yield ['ICD-10 Code', 'Description', 'Count', 'Primary Diagnoses', 'Status Distribution']
    
    # Get diagnoses within date range through medical records
    diagnoses = Diagnosis.objects.filter(
        medical_record__visit_date__range=[start_date, end_date]
    )
    
    # Group by diagnosis
    freq = diagnoses.values('icd10_code', 'description').annotate(
        total_count=Count('id'),
        primary_count=Count('id', filter=Q(is_primary=True)),
        active_count=Count('id', filter=Q(status='active')),
        resolved_count=Count('id', filter=Q(status='resolved')),
        chronic_count=Count('id', filter=Q(status='chronic'))
    ).order_by('-total_count')
    
    if scope == 'top_10':
        freq = freq[:10]
    elif scope == 'top_20':
        freq = freq[:20]
    else:
        freq = freq.filter(total_count__gte=min_occurrences)
    
    for item in freq.iterator():
        status_dist = f"Active: {item['active_count']}, Resolved: {item['resolved_count']}, Chronic: {item['chronic_count']}"
        yield [
            item['icd10_code'],
            item['description'][:100],
            item['total_count'],
            item['primary_count'],
            status_dist
        ]

def generate_prescription_analysis_csv(start_date, end_date, params):
    """Generator for prescription analysis CSV"""
    analysis_type = params.get('analysis_type', 'most_prescribed')
    
    yield ['Prescription Analysis Report']
    yield [f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"]
    yield []
    
    prescriptions = Prescription.objects.filter(
        prescribed_date__range=[start_date, end_date]
    ).select_related('medical_record__patient')
    
    if analysis_type == 'most_prescribed':
        yield ['Medication Name', 'Times Prescribed', 'Average Dosage', 'Total Quantity', 
               'Unique Patients', 'Active Prescriptions']
        
        med_stats = prescriptions.values('medication_name').annotate(
            count=Count('id'),
            avg_dosage=Avg('dosage'),
            total_quantity=Sum('quantity'),
            unique_patients=Count('medical_record__patient', distinct=True),
            active_count=Count('id', filter=Q(status='active'))
        ).order_by('-count')[:100]
        
        for item in med_stats.iterator():
            yield [
                item['medication_name'] or 'Unknown',
                item['count'],
                f"{item['avg_dosage']:.1f}" if item['avg_dosage'] else 'N/A',
                item['total_quantity'] or 0,
                item['unique_patients'],
                item['active_count']
            ]
    
    elif analysis_type == 'by_frequency':
        yield ['Frequency', 'Prescription Count', 'Average Dosage', 'Common Medications']
        
        freq_stats = prescriptions.values('frequency').annotate(
            count=Count('id'),
            avg_dosage=Avg('dosage')
        ).order_by('-count')
        
        for item in freq_stats.iterator():
            # Get top 3 medications for this frequency
            top_meds = prescriptions.filter(frequency=item['frequency']).values('medication_name').annotate(
                med_count=Count('id')
            ).order_by('-med_count')[:3]
            
            med_list = ', '.join([m['medication_name'] for m in top_meds if m['medication_name']])
            
            yield [
                item['frequency'] or 'Not specified',
                item['count'],
                f"{item['avg_dosage']:.1f}" if item['avg_dosage'] else 'N/A',
                med_list
            ]

def generate_lab_utilization_csv(start_date, end_date, params):
    """Generator for lab utilization CSV"""
    scope = params.get('scope', 'tests_ordered')
    
    yield ['Lab Utilization Report']
    yield [f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"]
    yield []
    
    if scope == 'tests_ordered':
        yield ['Test Name', 'Test Code', 'Times Ordered', 'Completed', 'Pending', 'Cancelled', 
               'Avg Turnaround (hours)']
        
        lab_orders = LabOrder.objects.filter(
            ordered_date__range=[start_date, end_date]
        )
        
        test_stats = lab_orders.values('test_name', 'test_code').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status__in=['ordered', 'collected', 'in_progress'])),
            cancelled=Count('id', filter=Q(status='cancelled'))
        ).order_by('-total')[:100]
        
        for item in test_stats.iterator():
            # Calculate average turnaround time for completed tests
            completed_orders = LabOrder.objects.filter(
                test_name=item['test_name'],
                status='completed',
                result__performed_date__isnull=False,
                ordered_date__range=[start_date, end_date]
            ).select_related('result')
            
            turnaround_sum = 0
            turnaround_count = 0
            for order in completed_orders.iterator():
                if order.result and order.result.performed_date:
                    turnaround = (order.result.performed_date - order.ordered_date).total_seconds() / 3600
                    turnaround_sum += turnaround
                    turnaround_count += 1
            
            avg_turnaround = turnaround_sum / turnaround_count if turnaround_count > 0 else 0
            
            yield [
                item['test_name'] or 'Unknown',
                item['test_code'] or 'N/A',
                item['total'],
                item['completed'],
                item['pending'],
                item['cancelled'],
                f"{avg_turnaround:.1f}"
            ]
    
    elif scope == 'abnormal_results':
        yield ['Test Name', 'Patient', 'Result Value', 'Reference Range', 'Unit', 'Performed Date']
        
        abnormal = LabResult.objects.filter(
            lab_order__ordered_date__range=[start_date, end_date],
            is_abnormal=True
        ).select_related('lab_order', 'lab_order__medical_record__patient').order_by('-performed_date')
        
        for result in abnormal.iterator():
            patient = result.lab_order.medical_record.patient if result.lab_order.medical_record else None
            yield [
                result.lab_order.test_name,
                patient.get_full_name() if patient else 'Unknown',
                result.result_value,
                result.reference_range,
                result.unit,
                result.performed_date.strftime('%Y-%m-%d %H:%M')
            ]

def generate_imaging_utilization_csv(start_date, end_date):
    """Generator for imaging utilization CSV"""
    yield ['Imaging Utilization Report']
    yield [f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"]
    yield []
    yield ['Imaging Type', 'Body Part', 'Times Ordered', 'Completed', 'Scheduled', 'Cancelled']
    
    imaging_orders = ImagingOrder.objects.filter(
        ordered_date__range=[start_date, end_date]
    )
    
    # Group by imaging type and body part
    stats = imaging_orders.values('imaging_type', 'body_part').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        scheduled=Count('id', filter=Q(status='scheduled')),
        cancelled=Count('id', filter=Q(status='cancelled'))
    ).order_by('-total')
    
    for item in stats.iterator():
        yield [
            item['imaging_type'] or 'Unknown',
            item['body_part'] or 'Not specified',
            item['total'],
            item['completed'],
            item['scheduled'],
            item['cancelled']
        ]

def generate_procedure_analysis_csv(start_date, end_date):
    """Generator for procedure analysis CSV"""
    yield ['Procedure Analysis Report']
    yield [f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"]
    yield []
    yield ['Procedure Name', 'Procedure Code', 'Times Performed', 'Completed', 'Scheduled', 'By Doctor']
    
    procedures = Procedure.objects.filter(
        date_performed__range=[start_date, end_date]
    ).select_related('performed_by')
    
    # Group by procedure
    proc_stats = procedures.values('procedure_name', 'procedure_code').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        scheduled=Count('id', filter=Q(status='scheduled'))
    ).order_by('-total')
    
    for item in proc_stats.iterator():
        # Get top doctor for this procedure
        top_doctor = procedures.filter(
            procedure_name=item['procedure_name']
        ).values('performed_by__first_name', 'performed_by__last_name').annotate(
            doc_count=Count('id')
        ).order_by('-doc_count').first()
        
        doctor_name = 'Unknown'
        if top_doctor and top_doctor.get('performed_by__first_name'):
            doctor_name = f"{top_doctor['performed_by__first_name']} {top_doctor['performed_by__last_name']}"
        
        yield [
            item['procedure_name'],
            item['procedure_code'],
            item['total'],
            item['completed'],
            item['scheduled'],
            doctor_name
        ]

def generate_patient_visit_summary_csv(start_date, end_date):
    """Generator for patient visit summary CSV"""
    yield ['Patient ID', 'Patient Name', 'Total Visits', 'First Visit', 'Last Visit', 
           'Total Diagnoses', 'Total Prescriptions', 'Total Lab Orders']
    
    patients = Patient.objects.filter(
        medical_records__visit_date__range=[start_date, end_date]
    ).distinct().iterator()
    
    for patient in patients:
        records = MedicalRecord.objects.filter(
            patient=patient,
            visit_date__range=[start_date, end_date]
        )
        
        first_visit = records.order_by('visit_date').first()
        last_visit = records.order_by('-visit_date').first()
        
        # Count related data
        diagnosis_count = Diagnosis.objects.filter(
            medical_record__in=records
        ).count()
        
        prescription_count = Prescription.objects.filter(
            medical_record__in=records
        ).count()
        
        lab_count = LabOrder.objects.filter(
            medical_record__in=records
        ).count()
        
        yield [
            patient.id,
            patient.get_full_name(),
            records.count(),
            first_visit.visit_date.strftime('%Y-%m-%d') if first_visit else 'N/A',
            last_visit.visit_date.strftime('%Y-%m-%d') if last_visit else 'N/A',
            diagnosis_count,
            prescription_count,
            lab_count
        ]