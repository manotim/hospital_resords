# hospital_records/apps/records/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from hospital_records.apps.patients.models import Patient
from .models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)
from .forms import (
    MedicalRecordForm, DiagnosisForm, PrescriptionForm,
    LabOrderForm, LabResultForm, ImagingOrderForm, ImagingResultForm,
    ProcedureForm, ClinicalNoteForm
)

# Import ALL decorators from accounts
from hospital_records.apps.accounts.decorators import (
    role_required, doctor_required, nurse_required, 
    clinical_staff_required, lab_tech_required, 
    medical_staff_required, admin_required, receptionist_required
)

from datetime import datetime, timedelta

@login_required
@clinical_staff_required
def record_list(request):
    """List all medical records - clinical staff only"""
    query = request.GET.get('q', '')
    record_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    user_type = request.user.profile.user_type
    
    records = MedicalRecord.objects.select_related('patient', 'doctor').all()
    
    # Role-based filtering
    if user_type == 'doctor':
        # Doctors see records they created
        records = records.filter(doctor=request.user)
    elif user_type == 'nurse':
        # Nurses see all records but with limited access
        records = records.all()
    
    if query:
        records = records.filter(
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(patient__patient_id__icontains=query) |
            Q(record_number__icontains=query) |
            Q(chief_complaint__icontains=query)
        )
    
    if record_type:
        records = records.filter(record_type=record_type)
    
    if date_from:
        records = records.filter(visit_date__date__gte=date_from)
    
    if date_to:
        records = records.filter(visit_date__date__lte=date_to)
    
    # Statistics
    total_records = records.count()
    today_records = records.filter(visit_date__date=timezone.now().date()).count()
    
    # Get patients for modal (limit for performance)
    patients = Patient.objects.all().order_by('first_name')[:100]
    
    context = {
        'records': records,
        'total_records': total_records,
        'today_records': today_records,
        'query': query,
        'record_type': record_type,
        'date_from': date_from,
        'date_to': date_to,
        'patients': patients,
        'user_type': user_type,
    }
    return render(request, 'records/record_list.html', context)

@login_required
@doctor_required
def create_medical_record(request, patient_id):
    """Create a new medical record - doctors only"""
    patient = get_object_or_404(Patient, pk=patient_id)
    next_action = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = request.user
            record.save()
            
            # Save diagnoses
            diagnoses_data = request.POST.getlist('diagnosis_description')
            icd10_codes = request.POST.getlist('icd10_code')
            for i, desc in enumerate(diagnoses_data):
                if desc:
                    Diagnosis.objects.create(
                        medical_record=record,
                        icd10_code=icd10_codes[i] if i < len(icd10_codes) else '',
                        description=desc,
                        is_primary=(i == 0)
                    )
            
            messages.success(request, f'Medical record created successfully for {patient.get_full_name()}')
            
            # Redirect based on next action
            if next_action == 'order_lab':
                return redirect('records:order_lab', record_id=record.pk)
            else:
                return redirect('records:record_detail', pk=record.pk)
    else:
        form = MedicalRecordForm(initial={'patient': patient})
    
    context = {
        'form': form,
        'patient': patient,
        'title': 'Create Medical Record',
        'is_doctor': True,
        'next_action': next_action,
    }
    return render(request, 'records/record_form.html', context)


@login_required
@clinical_staff_required
def record_detail(request, pk):
    """View medical record details"""
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient', 'doctor'),
        pk=pk
    )
    user_type = request.user.profile.user_type
    
    diagnoses = record.diagnoses.all()
    prescriptions = record.prescriptions.all()
    lab_orders = record.lab_orders.all()
    imaging_orders = record.imaging_orders.all()
    procedures = record.procedures.all()
    clinical_notes = record.clinical_notes.all()
    
    # Role-based data access
    if user_type == 'nurse':
        # Nurses see limited information
        context = {
            'record': record,
            'diagnoses': diagnoses,
            'prescriptions': prescriptions.filter(status='active'),  # Only active meds
            'lab_orders': lab_orders,
            'imaging_orders': imaging_orders,
            'procedures': procedures,
            'clinical_notes': clinical_notes.filter(note_type='nursing'),  # Only nursing notes
            'is_nurse_view': True,
            'can_add_nursing_note': True,
        }
    elif user_type == 'doctor':
        # Doctors see everything
        context = {
            'record': record,
            'diagnoses': diagnoses,
            'prescriptions': prescriptions,
            'lab_orders': lab_orders,
            'imaging_orders': imaging_orders,
            'procedures': procedures,
            'clinical_notes': clinical_notes,
            'is_doctor_view': True,
            'can_prescribe': True,
            'can_order_labs': True,
            'can_add_notes': True,
        }
    else:  # Admin
        context = {
            'record': record,
            'diagnoses': diagnoses,
            'prescriptions': prescriptions,
            'lab_orders': lab_orders,
            'imaging_orders': imaging_orders,
            'procedures': procedures,
            'clinical_notes': clinical_notes,
            'is_admin_view': True,
        }
    
    return render(request, 'records/record_detail.html', context)

@login_required
@doctor_required
def edit_record(request, pk):
    """Edit medical record - doctors only"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Ensure the doctor owns this record or is admin
    if record.doctor != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own records.')
        return redirect('records:record_detail', pk=record.pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record updated successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = MedicalRecordForm(instance=record)
    
    context = {
        'form': form,
        'record': record,
        'patient': record.patient, 
        'title': 'Edit Medical Record',
        'is_doctor': True,
    }
    return render(request, 'records/record_form.html', context)

@login_required
@clinical_staff_required
def print_record(request, pk):
    """Print-friendly view of medical record"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    return render(request, 'records/record_print.html', {'record': record})

@login_required
@doctor_required
def add_prescription(request, record_id):
    """Add prescription - doctors only"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.medical_record = record
            prescription.save()
            messages.success(request, 'Prescription added successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = PrescriptionForm()
    
    context = {
        'form': form,
        'record': record,
        'title': 'Add Prescription',
        'is_doctor': True,
    }
    return render(request, 'records/prescription_form.html', context)

@login_required
@doctor_required
def edit_prescription(request, pk):
    """Edit prescription - doctors only"""
    prescription = get_object_or_404(Prescription, pk=pk)
    record = prescription.medical_record
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription updated successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = PrescriptionForm(instance=prescription)
    
    context = {
        'form': form,
        'prescription': prescription,
        'record': record,
        'title': 'Edit Prescription',
    }
    return render(request, 'records/prescription_form.html', context)

@login_required
@doctor_required
def delete_prescription(request, pk):
    """Delete prescription - doctors only"""
    prescription = get_object_or_404(Prescription, pk=pk)
    record_pk = prescription.medical_record.pk
    
    if request.method == 'POST':
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully')
        return redirect('records:record_detail', pk=record_pk)
    
    return render(request, 'records/prescription_confirm_delete.html', {'prescription': prescription})


@login_required
@medical_staff_required  # Doctors, nurses, and lab techs can order labs
def order_lab(request, record_id):
    """Order laboratory test for an existing medical record"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    user_type = request.user.profile.user_type
    
    if request.method == 'POST':
        form = LabOrderForm(request.POST)
        if form.is_valid():
            lab_order = form.save(commit=False)
            lab_order.medical_record = record
            lab_order.ordered_by = request.user
            lab_order.save()
            messages.success(request, 'Lab test ordered successfully')
            return redirect('records:lab_detail', pk=lab_order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate form with record information if available
        initial_data = {
            'clinical_notes': f"Ordered for patient: {record.patient.get_full_name()}"
        }
        form = LabOrderForm(initial=initial_data)
    
    context = {
        'form': form,
        'record': record,
        'patient': record.patient,
        'title': f'Order Lab Test for {record.patient.get_full_name()}',
        'user_type': user_type,
    }
    return render(request, 'records/lab_order_form.html', context)


@login_required
@medical_staff_required
def lab_detail(request, pk):
    """View lab order details"""
    lab_order = get_object_or_404(LabOrder.objects.select_related('medical_record', 'ordered_by'), pk=pk)
    user_type = request.user.profile.user_type
    
    context = {
        'lab_order': lab_order,
        'user_type': user_type,
        'can_add_result': user_type == 'lab_tech' and lab_order.status != 'completed',
        'can_verify': user_type == 'doctor' and lab_order.result and not lab_order.result.verified_by,
    }
    return render(request, 'records/lab_detail.html', context)

@login_required
@lab_tech_required
def add_lab_result(request, pk):
    """Add result to lab order - lab techs only"""
    lab_order = get_object_or_404(LabOrder, pk=pk)
    
    # Prevent adding result if already completed
    if lab_order.status == 'completed':
        messages.warning(request, 'This lab order already has a result.')
        return redirect('records:lab_detail', pk=lab_order.pk)
    
    if request.method == 'POST':
        form = LabResultForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.lab_order = lab_order
            result.performed_by = request.user
            result.save()
            
            # Update lab order status
            lab_order.status = 'completed' if not result.is_abnormal else 'in_progress'
            lab_order.save()
            
            messages.success(request, 'Lab result added successfully')
            return redirect('records:lab_detail', pk=lab_order.pk)
    else:
        form = LabResultForm()
    
    context = {
        'form': form,
        'lab_order': lab_order,
        'title': 'Add Lab Result',
    }
    return render(request, 'records/lab_result_form.html', context)

@login_required
@doctor_required
def verify_lab_result(request, pk):
    """Verify lab result - doctors only"""
    result = get_object_or_404(LabResult, pk=pk)
    
    if result.verified_by:
        messages.warning(request, 'This result has already been verified.')
        return redirect('records:lab_detail', pk=result.lab_order.pk)
    
    if request.method == 'POST':
        result.verified_by = request.user
        result.verified_date = timezone.now()
        result.save()
        
        # Update lab order status
        result.lab_order.status = 'completed'
        result.lab_order.save()
        
        messages.success(request, 'Lab result verified successfully')
        return redirect('records:lab_detail', pk=result.lab_order.pk)
    
    return render(request, 'records/lab_verify.html', {'result': result})

@login_required
@medical_staff_required
def order_imaging(request, record_id):
    """Order imaging study"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
    if request.method == 'POST':
        form = ImagingOrderForm(request.POST)
        if form.is_valid():
            imaging_order = form.save(commit=False)
            imaging_order.medical_record = record
            imaging_order.ordered_by = request.user
            imaging_order.save()
            messages.success(request, 'Imaging study ordered successfully')
            return redirect('records:imaging_detail', pk=imaging_order.pk)
    else:
        form = ImagingOrderForm()
    
    context = {
        'form': form,
        'record': record,
        'title': 'Order Imaging Study'
    }
    return render(request, 'records/imaging_order_form.html', context)

@login_required
def imaging_detail(request, pk):
    """View imaging order details"""
    imaging_order = get_object_or_404(ImagingOrder.objects.select_related('medical_record', 'ordered_by'), pk=pk)
    
    context = {
        'imaging_order': imaging_order,
    }
    return render(request, 'records/imaging_detail.html', context)

@login_required
def add_imaging_result(request, pk):
    """Add result to imaging order"""
    imaging_order = get_object_or_404(ImagingOrder, pk=pk)
    
    if request.method == 'POST':
        form = ImagingResultForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.imaging_order = imaging_order
            result.radiologist = request.user
            result.save()
            
            # Update imaging order status
            imaging_order.status = 'completed'
            imaging_order.save()
            
            messages.success(request, 'Imaging result added successfully')
            return redirect('records:imaging_detail', pk=imaging_order.pk)
    else:
        form = ImagingResultForm()
    
    context = {
        'form': form,
        'imaging_order': imaging_order,
        'title': 'Add Imaging Result'
    }
    return render(request, 'records/imaging_result_form.html', context)

@login_required
def add_procedure(request, record_id):
    """Add procedure to medical record"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
    if request.method == 'POST':
        form = ProcedureForm(request.POST)
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.medical_record = record
            procedure.performed_by = request.user
            procedure.save()
            form.save_m2m()  # Save many-to-many for assisted_by
            messages.success(request, 'Procedure added successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = ProcedureForm()
    
    context = {
        'form': form,
        'record': record,
        'title': 'Add Procedure'
    }
    return render(request, 'records/procedure_form.html', context)

@login_required
def edit_procedure(request, pk):
    """Edit procedure"""
    procedure = get_object_or_404(Procedure, pk=pk)
    record = procedure.medical_record
    
    if request.method == 'POST':
        form = ProcedureForm(request.POST, instance=procedure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Procedure updated successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = ProcedureForm(instance=procedure)
    
    context = {
        'form': form,
        'procedure': procedure,
        'record': record,
        'title': 'Edit Procedure'
    }
    return render(request, 'records/procedure_form.html', context)



@login_required
@clinical_staff_required
def add_clinical_note(request, record_id):
    """Add clinical note - doctors and nurses"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    user_type = request.user.profile.user_type
    
    if request.method == 'POST':
        # 👇 IMPORTANT: Pass the user to the form here
        form = ClinicalNoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.medical_record = record
            note.author = request.user
            
            # FORCE the correct note type based on user role (backup validation)
            if user_type == 'nurse':
                note.note_type = 'nursing'
            
            note.save()
            messages.success(request, 'Clinical note added successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        # 👇 IMPORTANT: Pass the user to the form here for GET requests
        form = ClinicalNoteForm(user=request.user)
    
    context = {
        'form': form,
        'record': record,
        'title': 'Add Clinical Note',
        'user_type': user_type,
    }
    return render(request, 'records/clinical_note_form.html', context)



@login_required
def edit_clinical_note(request, pk):
    """Edit clinical note - only author can edit"""
    note = get_object_or_404(ClinicalNote, pk=pk)
    record = note.medical_record
    user_type = request.user.profile.user_type
    
    # Check if user is the author
    if note.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own notes.')
        return redirect('records:record_detail', pk=record.pk)
    
    if request.method == 'POST':
        # 👇 Pass user to form for edit too
        form = ClinicalNoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clinical note updated successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        # 👇 Pass user to form for edit GET
        form = ClinicalNoteForm(instance=note, user=request.user)
    
    context = {
        'form': form,
        'note': note,
        'record': record,
        'title': 'Edit Clinical Note',
        'user_type': user_type,
    }
    return render(request, 'records/clinical_note_form.html', context)



@login_required
def edit_clinical_note(request, pk):
    """Edit clinical note - only author can edit"""
    note = get_object_or_404(ClinicalNote, pk=pk)
    record = note.medical_record
    
    # Check if user is the author
    if note.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own notes.')
        return redirect('records:record_detail', pk=record.pk)
    
    if request.method == 'POST':
        form = ClinicalNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clinical note updated successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = ClinicalNoteForm(instance=note)
    
    context = {
        'form': form,
        'note': note,
        'record': record,
        'title': 'Edit Clinical Note',
    }
    return render(request, 'records/clinical_note_form.html', context)

@login_required
@clinical_staff_required
def api_recent_records(request):
    """API endpoint to get recent records"""
    limit = int(request.GET.get('limit', 50))
    records = MedicalRecord.objects.select_related('patient', 'doctor').order_by('-visit_date')[:limit]
    
    data = []
    for record in records:
        data.append({
            'id': record.id,
            'record_number': record.record_number,
            'patient_name': record.patient.get_full_name(),
            'patient_id': record.patient.patient_id,
            'visit_date': record.visit_date.strftime('%Y-%m-%d %H:%M'),
            'record_type': record.record_type,
            'record_type_display': record.get_record_type_display(),
        })
    
    return JsonResponse(data, safe=False)

@login_required
@doctor_required
def api_quick_create_record(request):
    """API to quickly create a basic medical record - doctors only"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            patient = get_object_or_404(Patient, pk=data['patient_id'])
            
            record = MedicalRecord.objects.create(
                patient=patient,
                doctor=request.user,
                record_type=data.get('record_type', 'consultation'),
                chief_complaint=data.get('chief_complaint', 'New visit'),
                history_of_present_illness='To be documented',
                assessment='Pending',
                plan='To be determined',
                visit_date=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'record_id': record.id,
                'record_number': record.record_number
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)



@login_required
@medical_staff_required
def quick_lab_order(request):
    """Order a lab test by automatically creating a minimal medical record"""
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        test_name = request.POST.get('test_name')
        test_code = request.POST.get('test_code')
        priority = request.POST.get('priority')
        clinical_notes = request.POST.get('clinical_notes')
        
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Create a minimal medical record automatically
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                doctor=request.user,
                record_type='lab_only',
                chief_complaint=f'Lab Test: {test_name}',
                history_of_present_illness='Ordered for laboratory investigation',
                assessment='Pending lab results',
                plan='Await lab results for further management',
                visit_date=timezone.now()
            )
            
            # Create the lab order linked to this record
            lab_order = LabOrder.objects.create(
                medical_record=medical_record,
                test_name=test_name,
                test_code=test_code,
                priority=priority,
                ordered_by=request.user,
                clinical_notes=clinical_notes,
                status='ordered'
            )
            
            messages.success(request, f'Lab test ordered successfully! A medical record #{medical_record.record_number} was automatically created.')
            return redirect('records:lab_detail', pk=lab_order.pk)
            
        except Patient.DoesNotExist:
            messages.error(request, 'Please select a valid patient.')
        except Exception as e:
            messages.error(request, f'Error ordering lab test: {str(e)}')
    
    # GET request - show the form
    patients = Patient.objects.all().order_by('first_name')
    recent_patients = patients[:10]
    
    context = {
        'patients': patients,
        'recent_patients': recent_patients,
        'title': 'Quick Lab Order',
    }
    return render(request, 'records/quick_lab_order.html', context)


@login_required
@medical_staff_required
def quick_lab_order_for_patient(request, patient_id):
    """Quick lab order for a specific patient"""
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        test_code = request.POST.get('test_code')
        priority = request.POST.get('priority')
        clinical_notes = request.POST.get('clinical_notes')
        
        # Create minimal medical record
        medical_record = MedicalRecord.objects.create(
            patient=patient,
            doctor=request.user,
            record_type='lab_only',
            chief_complaint=f'Lab Test: {test_name}',
            history_of_present_illness='Ordered for laboratory investigation',
            assessment='Pending lab results',
            plan='Await lab results for further management',
            visit_date=timezone.now()
        )
        
        # Create lab order
        lab_order = LabOrder.objects.create(
            medical_record=medical_record,
            test_name=test_name,
            test_code=test_code,
            priority=priority,
            ordered_by=request.user,
            clinical_notes=clinical_notes,
            status='ordered'
        )
        
        messages.success(request, f'Lab test ordered for {patient.get_full_name()}')
        return redirect('records:lab_detail', pk=lab_order.pk)
    
    context = {
        'patient': patient,
        'title': f'Quick Lab Order for {patient.get_full_name()}',
    }
    return render(request, 'records/quick_lab_order_form.html', context)




@login_required
@nurse_required
def nursing_notes(request):
    """Display nursing notes for the nurse"""
    user_type = request.user.profile.user_type
    
    # Get all clinical notes that are nursing notes
    nursing_notes = ClinicalNote.objects.filter(
        note_type='nursing'
    ).select_related(
        'medical_record__patient', 
        'author'
    ).order_by('-created_at')
    
    # Filter by current user if needed
    my_notes = request.GET.get('my_notes', False)
    if my_notes:
        nursing_notes = nursing_notes.filter(author=request.user)
    
    # Date filtering
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        nursing_notes = nursing_notes.filter(created_at__date__gte=date_from)
    if date_to:
        nursing_notes = nursing_notes.filter(created_at__date__lte=date_to)
    
    # Statistics
    total_notes = nursing_notes.count()
    today_notes = nursing_notes.filter(created_at__date=timezone.now().date()).count()
    my_notes_count = nursing_notes.filter(author=request.user).count()
    
    # Get patients for the modal - IMPORTANT: Filter to only patients with medical records
    patients = Patient.objects.filter(
        medical_records__isnull=False
    ).distinct().order_by('first_name')[:100]
    
    context = {
        'nursing_notes': nursing_notes,
        'total_notes': total_notes,
        'today_notes': today_notes,
        'my_notes_count': my_notes_count,
        'date_from': date_from,
        'date_to': date_to,
        'my_notes': my_notes,
        'user_type': user_type,
        'patients': patients,  # This is crucial for the modal
    }
    return render(request, 'records/nursing_notes.html', context)

