# hospital_records/apps/patients/forms.py
from django import forms
from .models import Patient, Admission, VitalSign
from django.contrib.auth.models import User

class PatientForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Format: YYYY-MM-DD'
    )
    
    class Meta:
        model = Patient
        exclude = ['patient_id', 'registration_date', 'updated_at', 'registered_by']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'chronic_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'primary_physician': forms.Select(attrs={'class': 'form-select'}),
            'insurance_provider': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_group_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make primary_physician NOT required
        self.fields['primary_physician'].required = False
        self.fields['primary_physician'].empty_label = "--- Select Doctor (Optional) ---"
        
        # Filter to show only doctors in the dropdown
        doctors = User.objects.filter(profile__user_type='doctor').order_by('first_name')
        self.fields['primary_physician'].queryset = doctors
        
        # Make other fields optional (though they already have blank=True in model)
        self.fields['allergies'].required = False
        self.fields['chronic_conditions'].required = False
        self.fields['current_medications'].required = False
        self.fields['insurance_provider'].required = False
        self.fields['insurance_policy_number'].required = False
        self.fields['insurance_group_number'].required = False
        
        # Add help text to clarify
        self.fields['primary_physician'].help_text = "Select a primary doctor for this patient (optional)"


class AdmissionForm(forms.ModelForm):
    admission_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    
    class Meta:
        model = Admission
        fields = ['admission_type', 'department', 'ward_number', 'bed_number', 'reason_for_admission']
        widgets = {
            'reason_for_admission': forms.Textarea(attrs={'rows': 3}),
        }

class VitalSignForm(forms.ModelForm):
    class Meta:
        model = VitalSign
        exclude = ['patient', 'recorded_by', 'recorded_at', 'bmi']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }