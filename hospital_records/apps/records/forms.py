from django import forms
from .models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)

class MedicalRecordForm(forms.ModelForm):
    visit_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    
    class Meta:
        model = MedicalRecord
        exclude = ['record_number', 'patient', 'doctor', 'created_at', 'updated_at']
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 3}),
            'history_of_present_illness': forms.Textarea(attrs={'rows': 4}),
            'review_of_systems': forms.Textarea(attrs={'rows': 3}),
            'physical_exam': forms.Textarea(attrs={'rows': 4}),
            'assessment': forms.Textarea(attrs={'rows': 4}),
            'plan': forms.Textarea(attrs={'rows': 4}),
            'follow_up_instructions': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['follow_up_date'].widget = forms.DateInput(attrs={'type': 'date'})

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        exclude = ['medical_record']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        exclude = ['medical_record', 'prescribed_date']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dosage'].widget.attrs['step'] = '0.01'

class LabOrderForm(forms.ModelForm):
    class Meta:
        model = LabOrder
        exclude = ['medical_record', 'ordered_by', 'ordered_date', 'status']
        widgets = {
            'clinical_notes': forms.Textarea(attrs={'rows': 3}),
        }

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        exclude = ['lab_order', 'performed_by', 'performed_date', 'verified_by', 'verified_date']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ImagingOrderForm(forms.ModelForm):
    class Meta:
        model = ImagingOrder
        exclude = ['medical_record', 'ordered_by', 'ordered_date', 'status']
        widgets = {
            'clinical_history': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})

class ImagingResultForm(forms.ModelForm):
    class Meta:
        model = ImagingResult
        exclude = ['imaging_order', 'radiologist', 'report_date']
        widgets = {
            'findings': forms.Textarea(attrs={'rows': 4}),
            'impression': forms.Textarea(attrs={'rows': 3}),
        }

class ProcedureForm(forms.ModelForm):
    date_performed = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    class Meta:
        model = Procedure
        exclude = ['medical_record']
        widgets = {
            'findings': forms.Textarea(attrs={'rows': 4}),
            'complications': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assisted_by'].widget.attrs['size'] = 5

class ClinicalNoteForm(forms.ModelForm):
    class Meta:
        model = ClinicalNote
        exclude = ['medical_record', 'author', 'created_at', 'updated_at']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
        }