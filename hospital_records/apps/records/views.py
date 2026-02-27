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
from datetime import datetime, timedelta

@login_required
def record_list(request):
    """List all medical records with filters"""
    query = request.GET.get('q', '')
    record_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    records = MedicalRecord.objects.select_related('patient', 'doctor').all()
    
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
    
    # Get all patients for the modal (you might want to limit this)
    patients = Patient.objects.all().order_by('first_name')[:100]  # Limit to 100 for performance
    
    context = {
        'records': records,
        'total_records': total_records,
        'today_records': today_records,
        'query': query,
        'record_type': record_type,
        'date_from': date_from,
        'date_to': date_to,
        'patients': patients,
    }
    return render(request, 'records/record_list.html', context)


@login_required
def create_medical_record(request, patient_id):
    """Create a new medical record for a patient"""
    patient = get_object_or_404(Patient, pk=patient_id)
    
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
                        is_primary=(i == 0)  # First diagnosis is primary
                    )
            
            messages.success(request, f'Medical record created successfully for {patient.get_full_name()}')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = MedicalRecordForm(initial={'patient': patient})
    
    context = {
        'form': form,
        'patient': patient,
        'title': 'Create Medical Record'
    }
    return render(request, 'records/record_form.html', context)

@login_required
def record_detail(request, pk):
    """View detailed medical record"""
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient', 'doctor'),
        pk=pk
    )
    
    diagnoses = record.diagnoses.all()
    prescriptions = record.prescriptions.all()
    lab_orders = record.lab_orders.all()
    imaging_orders = record.imaging_orders.all()
    procedures = record.procedures.all()
    clinical_notes = record.clinical_notes.all()
    
    context = {
        'record': record,
        'diagnoses': diagnoses,
        'prescriptions': prescriptions,
        'lab_orders': lab_orders,
        'imaging_orders': imaging_orders,
        'procedures': procedures,
        'clinical_notes': clinical_notes,
    }
    return render(request, 'records/record_detail.html', context)

@login_required
def edit_record(request, pk):
    """Edit medical record"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    
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
        'title': 'Edit Medical Record'
    }
    return render(request, 'records/record_form.html', context)

@login_required
def print_record(request, pk):
    """Print-friendly view of medical record"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    return render(request, 'records/record_print.html', {'record': record})

@login_required
def add_prescription(request, record_id):
    """Add prescription to medical record"""
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
        'title': 'Add Prescription'
    }
    return render(request, 'records/prescription_form.html', context)

@login_required
def edit_prescription(request, pk):
    """Edit prescription"""
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
        'title': 'Edit Prescription'
    }
    return render(request, 'records/prescription_form.html', context)

@login_required
def delete_prescription(request, pk):
    """Delete prescription"""
    prescription = get_object_or_404(Prescription, pk=pk)
    record_pk = prescription.medical_record.pk
    
    if request.method == 'POST':
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully')
        return redirect('records:record_detail', pk=record_pk)
    
    return render(request, 'records/prescription_confirm_delete.html', {'prescription': prescription})

@login_required
def order_lab(request, record_id):
    """Order laboratory test"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
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
        form = LabOrderForm()
    
    context = {
        'form': form,
        'record': record,
        'title': 'Order Lab Test'
    }
    return render(request, 'records/lab_order_form.html', context)

@login_required
def lab_detail(request, pk):
    """View lab order details"""
    lab_order = get_object_or_404(LabOrder.objects.select_related('medical_record', 'ordered_by'), pk=pk)
    
    context = {
        'lab_order': lab_order,
    }
    return render(request, 'records/lab_detail.html', context)

@login_required
def add_lab_result(request, pk):
    """Add result to lab order"""
    lab_order = get_object_or_404(LabOrder, pk=pk)
    
    if request.method == 'POST':
        form = LabResultForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.lab_order = lab_order
            result.performed_by = request.user
            result.save()
            
            # Update lab order status
            lab_order.status = 'completed'
            lab_order.save()
            
            messages.success(request, 'Lab result added successfully')
            return redirect('records:lab_detail', pk=lab_order.pk)
    else:
        form = LabResultForm()
    
    context = {
        'form': form,
        'lab_order': lab_order,
        'title': 'Add Lab Result'
    }
    return render(request, 'records/lab_result_form.html', context)

@login_required
def verify_lab_result(request, pk):
    """Verify lab result"""
    result = get_object_or_404(LabResult, pk=pk)
    
    if request.method == 'POST':
        result.verified_by = request.user
        result.verified_date = timezone.now()
        result.save()
        messages.success(request, 'Lab result verified successfully')
        return redirect('records:lab_detail', pk=result.lab_order.pk)
    
    return render(request, 'records/lab_verify.html', {'result': result})

@login_required
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
def add_clinical_note(request, record_id):
    """Add clinical note to medical record"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
    if request.method == 'POST':
        form = ClinicalNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.medical_record = record
            note.author = request.user
            note.save()
            messages.success(request, 'Clinical note added successfully')
            return redirect('records:record_detail', pk=record.pk)
    else:
        form = ClinicalNoteForm()
    
    context = {
        'form': form,
        'record': record,
        'title': 'Add Clinical Note'
    }
    return render(request, 'records/clinical_note_form.html', context)

@login_required
def edit_clinical_note(request, pk):
    """Edit clinical note"""
    note = get_object_or_404(ClinicalNote, pk=pk)
    record = note.medical_record
    
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
        'title': 'Edit Clinical Note'
    }
    return render(request, 'records/clinical_note_form.html', context)


@login_required
def api_recent_records(request):
    """API endpoint to get recent records for the modal"""
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
def api_quick_create_record(request):
    """API to quickly create a basic medical record"""
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

