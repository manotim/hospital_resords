# patients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import Patient, Admission, VitalSign
from django.http import JsonResponse
from .forms import PatientForm, AdmissionForm, VitalSignForm
from datetime import datetime, timedelta

@login_required
def dashboard(request):
    # Statistics
    total_patients = Patient.objects.count()
    active_patients = Patient.objects.filter(status='active').count()
    discharged_today = Patient.objects.filter(
        status='discharged',
        admissions__discharge_date__date=timezone.now().date()
    ).count()
    new_admissions = Patient.objects.filter(
        admissions__admission_date__date=timezone.now().date()
    ).count()
    
    # Recent patients
    recent_patients = Patient.objects.order_by('-registration_date')[:10]
    
    # Current admissions
    current_admissions = Admission.objects.filter(is_active=True).select_related('patient', 'admitting_doctor')[:10]
    
    # Patients by department
    departments = Admission.objects.filter(is_active=True).values('department').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'total_patients': total_patients,
        'active_patients': active_patients,
        'discharged_today': discharged_today,
        'new_admissions': new_admissions,
        'recent_patients': recent_patients,
        'current_admissions': current_admissions,
        'departments': departments,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
def patient_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    patients = Patient.objects.all()
    
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    if status_filter:
        patients = patients.filter(status=status_filter)
    
    context = {
        'patients': patients,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'patients/patient_list.html', context)

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    admissions = patient.admissions.all()[:5]
    vitals = patient.vitals.all()[:10]
    
    context = {
        'patient': patient,
        'admissions': admissions,
        'vitals': vitals,
    }
    return render(request, 'patients/patient_detail.html', context)


@login_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.registered_by = request.user
            patient.save()
            messages.success(request, f'Patient {patient.get_full_name()} registered successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
        else:
            # Add this for debugging
            print("Form errors:", form.errors)
            # You can also show errors in the template
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientForm()
    
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Register New Patient'})


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'patients/patient_form.html', {'form': form, 'patient': patient, 'title': 'Edit Patient'})

@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient_name = patient.get_full_name()
        patient.delete()
        messages.success(request, f'Patient {patient_name} has been deleted.')
        return redirect('patients:patient_list')
    
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})

@login_required
def admit_patient(request, pk):
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
            
            # Update patient status
            patient.status = 'active'
            patient.save()
            
            messages.success(request, f'Patient {patient.get_full_name()} admitted successfully!')
            return redirect('patients:patient_detail', pk=patient.pk)
    else:
        form = AdmissionForm()
    
    return render(request, 'patients/admit_form.html', {'form': form, 'patient': patient})

@login_required
def discharge_patient(request, pk):
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
    
    return render(request, 'patients/discharge_form.html', {'patient': patient, 'admission': admission})

@login_required
def add_vitals(request, pk):
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
    
    return render(request, 'patients/vitals_form.html', {'form': form, 'patient': patient})


@login_required
def api_patients(request):
    """API endpoint to get patients for modals"""
    try:
        # Get search query if provided
        query = request.GET.get('q', '')
        
        patients = Patient.objects.all().order_by('first_name')
        
        # Apply search if query exists
        if query:
            patients = patients.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(phone_number__icontains=query)
            )
        
        # Limit results for performance
        patients = patients[:100]
        
        data = []
        for patient in patients:
            data.append({
                'id': patient.id,
                'patient_id': patient.patient_id,
                'full_name': patient.get_full_name(),
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'email': patient.email or '',
                'age': patient.age(),
                'gender': patient.get_gender_display(),
                'gender_code': patient.gender,
                'phone_number': patient.phone_number,
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
