# hospital_records/apps/patients/views_dashboards.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from hospital_records.apps.records.models import MedicalRecord, Prescription, LabOrder, ClinicalNote
from .models import Patient, Admission, VitalSign
from hospital_records.apps.records.models import MedicalRecord, Prescription, LabOrder
from hospital_records.apps.accounts.decorators import doctor_required, nurse_required, receptionist_required, lab_tech_required

@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor-specific dashboard"""
    today = timezone.now().date()
    user = request.user
    
    # Today's appointments/consultations
    today_appointments = MedicalRecord.objects.filter(
        doctor=user,
        visit_date__date=today
    ).count()
    
    # Pending lab results
    pending_lab_results = LabOrder.objects.filter(
        medical_record__doctor=user,
        status__in=['ordered', 'collected', 'in_progress']
    ).count()
    
    # Active patients under this doctor
    my_patients = Patient.objects.filter(
        primary_physician=user,
        status='active'
    ).count()
    
    # Recent patients seen
    recent_patients = MedicalRecord.objects.filter(
        doctor=user
    ).select_related('patient').order_by('-visit_date')[:10]
    
    # Active prescriptions
    active_prescriptions = Prescription.objects.filter(
        medical_record__doctor=user,
        status='active'
    ).count()
    
    # Patients with pending lab results
    patients_pending_labs = Patient.objects.filter(
        medical_records__lab_orders__status__in=['ordered', 'collected'],
        medical_records__doctor=user
    ).distinct().count()
    
    # Weekly statistics
    week_ago = timezone.now() - timedelta(days=7)
    weekly_stats = {
        'consultations': MedicalRecord.objects.filter(
            doctor=user,
            visit_date__gte=week_ago
        ).count(),
        'prescriptions': Prescription.objects.filter(
            medical_record__doctor=user,
            prescribed_date__gte=week_ago
        ).count(),
        'lab_orders': LabOrder.objects.filter(
            ordered_by=user,
            ordered_date__gte=week_ago
        ).count(),
    }
    
    context = {
        'today_appointments': today_appointments,
        'pending_lab_results': pending_lab_results,
        'my_patients': my_patients,
        'recent_patients': recent_patients,
        'active_prescriptions': active_prescriptions,
        'patients_pending_labs': patients_pending_labs,
        'weekly_stats': weekly_stats,
    }
    return render(request, 'patients/doctor_dashboard.html', context)

@login_required
@nurse_required
def nurse_dashboard(request):
    """Nurse-specific dashboard"""
    today = timezone.now().date()
    user = request.user
    
    # Patients needing vitals today
    patients_with_vitals_today = VitalSign.objects.filter(
        recorded_at__date=today
    ).values_list('patient', flat=True).distinct()
    
    pending_vitals = Patient.objects.filter(
        status='active'
    ).exclude(
        id__in=patients_with_vitals_today
    ).count()
    
    # Today's vitals recorded
    vitals_today = VitalSign.objects.filter(
        recorded_by=user,
        recorded_at__date=today
    ).count()
    
    # Current admissions
    current_admissions = Admission.objects.filter(
        is_active=True
    ).select_related('patient', 'admitting_doctor')[:15]
    
    # Medications due today
    medications_today = Prescription.objects.filter(
        status='active',
        prescribed_date__date=today
    ).count()
    
    # Nursing notes added today
    nursing_notes_today = ClinicalNote.objects.filter(
        author=user,
        note_type='nursing',
        created_at__date=today
    ).count()
    
    # Patient list needing attention (abnormal vitals) - WITH ERROR HANDLING
    try:
        abnormal_vitals = VitalSign.objects.filter(
            recorded_at__date=today,
            oxygen_saturation__lt=95
        ).select_related('patient')[:10]
    except:
        # Fallback if there's an error
        abnormal_vitals = []
    
    # Recent vitals recorded - WITH ERROR HANDLING
    try:
        recent_vitals = VitalSign.objects.filter(
            recorded_by=user
        ).select_related('patient').order_by('-recorded_at')[:10]
    except:
        recent_vitals = []
    
    # Active patients list for modal
    active_patients_list = Patient.objects.filter(
        status='active'
    ).order_by('first_name')[:50]
    
    # Patients for the modal
    patients = Patient.objects.filter(
        medical_records__isnull=False
    ).distinct().order_by('first_name')[:100]
    
    # Active patients count
    active_patients = Patient.objects.filter(status='active').count()
    
    context = {
        'pending_vitals': pending_vitals,
        'vitals_today': vitals_today,
        'current_admissions': current_admissions,
        'medications_today': medications_today,
        'nursing_notes_today': nursing_notes_today,
        'abnormal_vitals': abnormal_vitals,
        'recent_vitals': recent_vitals,
        'active_patients_list': active_patients_list,
        'patients': patients,
        'active_patients': active_patients,
    }
    return render(request, 'patients/nurse_dashboard.html', context)



@login_required
@receptionist_required
def reception_dashboard(request):
    """Receptionist-specific dashboard"""
    today = timezone.now().date()
    
    # Today's registrations
    new_registrations = Patient.objects.filter(
        registration_date__date=today
    ).count()
    
    # Today's admissions
    today_admissions = Admission.objects.filter(
        admission_date__date=today
    ).count()
    
    # Today's discharges
    today_discharges = Patient.objects.filter(
        status='discharged',
        admissions__discharge_date__date=today
    ).count()
    
    # Active patients
    active_patients = Patient.objects.filter(status='active').count()
    
    # Department-wise admission counts
    department_admissions = Admission.objects.filter(
        is_active=True
    ).values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent registrations
    recent_registrations = Patient.objects.order_by('-registration_date')[:10]
    
    # Insurance verification needed (example)
    insurance_pending = Patient.objects.filter(
        insurance_provider='',
        status='active'
    ).count()
    
    context = {
        'new_registrations': new_registrations,
        'today_admissions': today_admissions,
        'today_discharges': today_discharges,
        'active_patients': active_patients,
        'department_admissions': department_admissions,
        'recent_registrations': recent_registrations,
        'insurance_pending': insurance_pending,
    }
    return render(request, 'patients/reception_dashboard.html', context)

@login_required
@lab_tech_required
def lab_dashboard(request):
    """Lab Technician-specific dashboard"""
    today = timezone.now().date()
    user = request.user
    
    # Pending lab orders
    pending_orders = LabOrder.objects.filter(
        status='ordered'
    ).select_related('medical_record__patient', 'ordered_by').count()
    
    # Collected samples waiting for processing
    collected_samples = LabOrder.objects.filter(
        status='collected'
    ).select_related('medical_record__patient').count()
    
    # Completed tests today
    completed_today = LabOrder.objects.filter(
        status='completed',
        result__performed_date__date=today
    ).count()
    
    # My pending assignments
    my_pending = LabOrder.objects.filter(
        status='in_progress',
        collected_by=user
    ).count()
    
    # Urgent/STAT orders
    urgent_orders = LabOrder.objects.filter(
        priority__in=['urgent', 'stat'],
        status__in=['ordered', 'collected']
    ).select_related('medical_record__patient')[:10]
    
    # Recent lab orders
    recent_orders = LabOrder.objects.filter(
        ordered_date__date=today
    ).select_related('medical_record__patient', 'ordered_by')[:15]
    
    # Test type statistics
    test_stats = LabOrder.objects.filter(
        ordered_date__date=today
    ).values('test_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'pending_orders': pending_orders,
        'collected_samples': collected_samples,
        'completed_today': completed_today,
        'my_pending': my_pending,
        'urgent_orders': urgent_orders,
        'recent_orders': recent_orders,
        'test_stats': test_stats,
    }
    return render(request, 'patients/lab_dashboard.html', context)