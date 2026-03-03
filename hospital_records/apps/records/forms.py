# forms.py
from django import forms
from .models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)

class MedicalRecordForm(forms.ModelForm):
    visit_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        required=False,
        label="Visit Date & Time"
    )
    
    class Meta:
        model = MedicalRecord
        exclude = ['record_number', 'patient', 'doctor', 'created_at', 'updated_at']
        widgets = {
            'record_type': forms.Select(attrs={'class': 'form-select'}),
            'chief_complaint': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'history_of_present_illness': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'review_of_systems': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'physical_exam': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'assessment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'plan': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'follow_up_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['follow_up_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        self.fields['follow_up_date'].required = False
        self.fields['review_of_systems'].required = False
        self.fields['physical_exam'].required = False
        self.fields['follow_up_instructions'].required = False

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        exclude = ['medical_record']
        widgets = {
            'icd10_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., J45.909'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Diagnosis description'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        exclude = ['medical_record', 'prescribed_date']
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medication name'}),
            'dosage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dosage_unit': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'route': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Oral, IV'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7 days'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'refills': forms.NumberInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class LabOrderForm(forms.ModelForm):
    class Meta:
        model = LabOrder
        exclude = ['medical_record', 'ordered_by', 'ordered_date']
        widgets = {
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'test_code': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'collected_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'collected_by': forms.Select(attrs={'class': 'form-select'}),
            'specimen_type': forms.TextInput(attrs={'class': 'form-control'}),
            'clinical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        exclude = ['lab_order', 'performed_by', 'performed_date', 'verified_by', 'verified_date']
        widgets = {
            'result_value': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_range': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'is_abnormal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'result_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ImagingOrderForm(forms.ModelForm):
    scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = ImagingOrder
        exclude = ['medical_record', 'ordered_by', 'ordered_date']
        widgets = {
            'imaging_type': forms.Select(attrs={'class': 'form-select'}),
            'body_part': forms.TextInput(attrs={'class': 'form-control'}),
            'clinical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class ImagingResultForm(forms.ModelForm):
    class Meta:
        model = ImagingResult
        exclude = ['imaging_order', 'radiologist', 'report_date']
        widgets = {
            'findings': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'impression': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'image_file': forms.FileInput(attrs={'class': 'form-control'}),
            'report_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProcedureForm(forms.ModelForm):
    date_performed = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    
    class Meta:
        model = Procedure
        exclude = ['medical_record']
        widgets = {
            'procedure_name': forms.TextInput(attrs={'class': 'form-control'}),
            'procedure_code': forms.TextInput(attrs={'class': 'form-control'}),
            'performed_by': forms.Select(attrs={'class': 'form-select'}),
            'assisted_by': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'findings': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'complications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }





class ClinicalNoteForm(forms.ModelForm):
    class Meta:
        model = ClinicalNote
        fields = ['note_type', 'content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'note_type': forms.Select(attrs={'class': 'form-select'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pop the user from kwargs (it's passed from the view)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is a nurse, set default to nursing and make field read-only
        if user and hasattr(user, 'profile') and user.profile.user_type == 'nurse':
            self.fields['note_type'].initial = 'nursing'
            self.fields['note_type'].disabled = True  # Nurses can't change note type
            self.fields['note_type'].help_text = "Nurses can only create nursing notes"
            
            # Hide is_private for nurses (optional)
            self.fields['is_private'].widget = forms.HiddenInput()
            self.fields['is_private'].initial = False
        
        # For doctors, make all fields available
        elif user and hasattr(user, 'profile') and user.profile.user_type == 'doctor':
            self.fields['note_type'].help_text = "Select the type of clinical note"

