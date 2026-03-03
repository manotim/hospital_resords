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
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Doe'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g., patient@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., NY'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 10001'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1234567890'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Spouse, Parent'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List any known allergies (e.g., Penicillin, Peanuts)'}),
            'chronic_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Diabetes, Hypertension'}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List current medications and dosages'}),
            'primary_physician': forms.Select(attrs={'class': 'form-select'}),
            'insurance_provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Insurance company name'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Policy number'}),
            'insurance_group_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group number'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make primary_physician NOT required
        self.fields['primary_physician'].required = False
        self.fields['primary_physician'].empty_label = "--- Select Doctor (Optional) ---"
        
        # Filter to show only doctors in the dropdown
        doctors = User.objects.filter(profile__user_type='doctor').order_by('first_name')
        self.fields['primary_physician'].queryset = doctors
        
        # Make other fields optional
        self.fields['allergies'].required = False
        self.fields['chronic_conditions'].required = False
        self.fields['current_medications'].required = False
        self.fields['insurance_provider'].required = False
        self.fields['insurance_policy_number'].required = False
        self.fields['insurance_group_number'].required = False
        
        # Add help text
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
            'admission_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Cardiology'}),
            'ward_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ward A'}),
            'bed_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101-B'}),
            'reason_for_admission': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Reason for admission...'}),
        }


class VitalSignForm(forms.ModelForm):
    class Meta:
        model = VitalSign
        exclude = ['patient', 'recorded_by', 'recorded_at', 'bmi']
        widgets = {
            'blood_pressure_systolic': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '120', 
                'min': 70, 
                'max': 250,
                'title': 'Systolic pressure (top number)'
            }),
            'blood_pressure_diastolic': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '80', 
                'min': 40, 
                'max': 150,
                'title': 'Diastolic pressure (bottom number)'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '75', 
                'min': 30, 
                'max': 250,
                'title': 'Beats per minute'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '98.6', 
                'step': '0.1', 
                'min': 95, 
                'max': 106,
                'title': 'Temperature in Fahrenheit'
            }),
            'respiratory_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '16', 
                'min': 8, 
                'max': 40,
                'title': 'Breaths per minute'
            }),
            'oxygen_saturation': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '98', 
                'min': 70, 
                'max': 100,
                'title': 'Oxygen saturation percentage'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '170.0', 
                'step': '0.1', 
                'min': 30, 
                'max': 250,
                'title': 'Height in centimeters (cm)'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '70.0', 
                'step': '0.1', 
                'min': 1, 
                'max': 300,
                'title': 'Weight in kilograms (kg)'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Additional notes (e.g., patient position, any concerns...)'
            }),
        }
    
    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp and (temp < 95 or temp > 106):
            raise forms.ValidationError("Temperature must be between 95°F and 106°F")
        return temp
    
    def clean_oxygen_saturation(self):
        spo2 = self.cleaned_data.get('oxygen_saturation')
        if spo2 and (spo2 < 70 or spo2 > 100):
            raise forms.ValidationError("Oxygen saturation must be between 70% and 100%")
        return spo2
    
    def clean_blood_pressure_systolic(self):
        value = self.cleaned_data.get('blood_pressure_systolic')
        if value and (value < 70 or value > 250):
            raise forms.ValidationError("Systolic pressure must be between 70 and 250")
        return value
    
    def clean_blood_pressure_diastolic(self):
        value = self.cleaned_data.get('blood_pressure_diastolic')
        if value and (value < 40 or value > 150):
            raise forms.ValidationError("Diastolic pressure must be between 40 and 150")
        return value
    
    def clean_heart_rate(self):
        value = self.cleaned_data.get('heart_rate')
        if value and (value < 30 or value > 250):
            raise forms.ValidationError("Heart rate must be between 30 and 250 bpm")
        return value
    
    def clean_respiratory_rate(self):
        value = self.cleaned_data.get('respiratory_rate')
        if value and (value < 8 or value > 40):
            raise forms.ValidationError("Respiratory rate must be between 8 and 40 breaths/min")
        return value
    
    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height and (height < 30 or height > 250):
            raise forms.ValidationError("Height must be between 30cm and 250cm")
        return height
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and (weight < 1 or weight > 300):
            raise forms.ValidationError("Weight must be between 1kg and 300kg")
        return weight