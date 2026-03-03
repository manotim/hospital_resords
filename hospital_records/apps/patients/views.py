# hospital_records/apps/patients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import Patient, Admission, VitalSign
from django.http import JsonResponse
from .forms import PatientForm, AdmissionForm, VitalSignForm
from hospital_records.apps.accounts.decorators import (
    role_required, clinical_staff_required, receptionist_required, 
    nurse_required, doctor_required, medical_staff_required
)
from datetime import datetime, timedelta

@login_required
def dashboard(request):
    """Main dashboard - redirects to role-specific dashboard"""
    if not hasattr(request.user, 'profile'):
        messages.warning(request, 'Please complete your profile first.')
        return redirect('accounts:edit_profile')
    
    user_type = request.user.profile.user_type
    
    # Redirect to role-specific dashboards
    if user_type == 'doctor':
        return redirect('patients:doctor_dashboard')
    elif user_type == 'nurse':
        return redirect('patients:nurse_dashboard')
    elif user_type == 'receptionist':
        return redirect('patients:reception_dashboard')
    elif user_type == 'lab_tech':
        return redirect('patients:lab_dashboard')
    else:
        # Admin dashboard
        return render(request, 'patients/dashboard.html', get_admin_dashboard_stats(request))

# In hospital_records/apps/patients/views.py, update the patient_list view:

@login_required
@role_required(['admin', 'doctor', 'nurse', 'receptionist', 'lab_tech'])
def patient_list(request):
    """All staff can view patient list with appropriate filters"""
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    action = request.GET.get('action', '')  # Get the action parameter
    user_type = request.user.profile.user_type
    
    patients = Patient.objects.all()
    
    # Apply role-based filters
    if user_type == 'doctor':
        patients = patients.filter(Q(primary_physician=request.user) | Q(primary_physician__isnull=True))
    
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    if status_filter:
        patients = patients.filter(status=status_filter)
    
    # Get medical records for each patient if needed for actions
    if action in ['order_lab', 'add_prescription']:
        # For these actions, we need to show patients with existing records
        patients = patients.filter(medical_records__isnull=False).distinct()
    
    context = {
        'patients': patients,
        'query': query,
        'status_filter': status_filter,
        'action': action,
        'user_type': user_type,
    }
    return render(request, 'patients/patient_list.html', context)



@login_required
@clinical_staff_required  # Doctors and nurses only
def patient_detail(request, pk):
    """Clinical staff can view full patient details"""
    patient = get_object_or_404(Patient, pk=pk)
    user_type = request.user.profile.user_type
    
    # Role-based data access
    if user_type == 'nurse':
        # Nurses see limited information
        admissions = patient.admissions.filter(is_active=True)[:5]
        vitals = patient.vitals.all()[:10]
        context = {
            'patient': patient,
            'admissions': admissions,
            'vitals': vitals,
            'is_nurse_view': True,
            'can_record_vitals': True,
            'can_add_nursing_notes': True,
        }
    else:  # Doctors and admins
        admissions = patient.admissions.all()[:5]
        vitals = patient.vitals.all()[:10]
        context = {
            'patient': patient,
            'admissions': admissions,
            'vitals': vitals,
            'is_doctor_view': True,
            'can_create_records': True,
            'can_order_labs': True,
            'can_prescribe': True,
        }
    
    return render(request, 'patients/patient_detail.html', context)

@login_required
@receptionist_required
def patient_add(request):
    """Register new patient - receptionist only"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.registered_by = request.user
            patient.save()
            messages.success(request, f'Patient {patient.get_full_name()} registered successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientForm()
    
    return render(request, 'patients/patient_form.html', {
        'form': form, 
        'title': 'Register New Patient',
        'is_receptionist': True
    })

@login_required
@clinical_staff_required
def patient_edit(request, pk):
    """Edit patient information - clinical staff only"""
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'patients/patient_form.html', {
        'form': form, 
        'patient': patient, 
        'title': 'Edit Patient',
        'is_editing': True
    })

@login_required
@role_required(['admin'])  # Only admins can delete patients
def patient_delete(request, pk):
    """Delete patient - admin only"""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Prevent deletion if patient has active records
    if patient.medical_records.exists():
        messages.error(request, 'Cannot delete patient with existing medical records.')
        return redirect('patients:patient_detail', pk=patient.pk)
    
    if request.method == 'POST':
        patient_name = patient.get_full_name()
        patient.delete()
        messages.success(request, f'Patient {patient_name} has been deleted.')
        return redirect('patients:patient_list')
    
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})

@login_required
@clinical_staff_required
def admit_patient(request, pk):
    """Admit patient - doctors and nurses"""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check if patient is already admitted
    if Admission.objects.filter(patient=patient, is_active=True).exists():
        messages.warning(request, 'Patient is already admitted.')
        return redirect('patients:patient_detail', pk=patient.pk)
    
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.patient = patient
            admission.admitting_doctor = request.user
            admission.save()
            
            patient.status = 'active'
            patient.save()
            
            messages.success(request, f'Patient {patient.get_full_name()} admitted successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
    else:
        form = AdmissionForm()
    
    return render(request, 'patients/admit_form.html', {
        'form': form, 
        'patient': patient,
        'user_type': request.user.profile.user_type
    })

@login_required
@doctor_required  # Only doctors can discharge
def discharge_patient(request, pk):
    """Discharge patient - doctors only"""
    patient = get_object_or_404(Patient, pk=pk)
    admission = Admission.objects.filter(patient=patient, is_active=True).first()
    
    if not admission:
        messages.warning(request, 'Patient is not currently admitted.')
        return redirect('patients:patient_detail', pk=patient.pk)
    
    if request.method == 'POST':
        discharge_type = request.POST.get('discharge_type')
        discharge_summary = request.POST.get('discharge_summary')
        
        admission.is_active = False
        admission.discharge_date = timezone.now()
        admission.discharge_type = discharge_type
        admission.discharge_summary = discharge_summary
        admission.save()
        
        patient.status = 'discharged'
        patient.save()
        
        messages.success(request, f'Patient {patient.get_full_name()} discharged successfully!')
        return redirect('patients:patient_detail', pk=patient.pk)
    
    return render(request, 'patients/discharge_form.html', {
        'patient': patient, 
        'admission': admission
    })

@login_required
@nurse_required  # Primarily nurses record vitals
def add_vitals(request, pk):
    """Record vital signs - nurses"""
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = VitalSignForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.patient = patient
            vitals.recorded_by = request.user
            vitals.save()
            
            messages.success(request, 'Vital signs recorded successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
    else:
        form = VitalSignForm()
    
    return render(request, 'patients/vitals_form.html', {
        'form': form, 
        'patient': patient,
        'is_nurse': True
    })

# Helper function for admin dashboard
def get_admin_dashboard_stats(request):
    """Get statistics for admin dashboard"""
    from datetime import date
    
    today = date.today()
    
    context = {
        'total_patients': Patient.objects.count(),
        'active_patients': Patient.objects.filter(status='active').count(),
        'discharged_today': Patient.objects.filter(
            status='discharged',
            admissions__discharge_date__date=today
        ).count(),
        'new_admissions': Patient.objects.filter(
            admissions__admission_date__date=today
        ).count(),
        'recent_patients': Patient.objects.order_by('-registration_date')[:10],
        'current_admissions': Admission.objects.filter(is_active=True).select_related('patient', 'admitting_doctor')[:10],
        'departments': Admission.objects.filter(is_active=True).values('department').annotate(
            count=Count('id')
        ).order_by('-count')[:5],
    }
    return context