from django import forms
from .models import ReportTemplate, GeneratedReport, ScheduledReport, DashboardWidget
from hospital_records.apps.patients.models import Patient
from hospital_records.apps.records.models import MedicalRecord, Diagnosis, Prescription
from django.contrib.auth.models import User
import json

class DateRangeForm(forms.Form):
    """Base form for date range selection"""
    date_range = forms.ChoiceField(
        choices=[
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('this_week', 'This Week'),
            ('last_week', 'Last Week'),
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
            ('this_quarter', 'This Quarter'),
            ('last_quarter', 'Last Quarter'),
            ('this_year', 'This Year'),
            ('last_year', 'Last Year'),
            ('custom', 'Custom Range'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'dateRangeSelect'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

class ReportGenerationForm(forms.Form):
    """Form for generating reports"""
    REPORT_CHOICES = [
        ('patient_census', 'Patient Census Report'),
        ('admission_discharge', 'Admission & Discharge Summary'),
        ('diagnosis_frequency', 'Diagnosis Frequency Report'),
        ('prescription_analysis', 'Prescription Analysis'),
        ('lab_utilization', 'Laboratory Utilization'),
        ('imaging_utilization', 'Imaging Utilization'),
        ('patient_demographics', 'Patient Demographics'),
        ('length_of_stay', 'Length of Stay Analysis'),
        ('readmission_rate', 'Readmission Rate'),
        ('mortality_rate', 'Mortality Rate'),
        ('physician_workload', 'Physician Workload'),
        ('department_performance', 'Department Performance'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('html', 'HTML'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter report title'})
    )
    
    # Optional filters
    department = forms.ChoiceField(
        choices=[('', 'All Departments')] + [(dept, dept) for dept in 
            ['Emergency', 'Cardiology', 'Pediatrics', 'Orthopedics', 'Neurology', 'Oncology', 'General']],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    physician = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Doctors').distinct(),
        required=False,
        empty_label="All Physicians",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    patient_demographics = forms.MultipleChoiceField(
        choices=[
            ('age_group', 'By Age Group'),
            ('gender', 'By Gender'),
            ('blood_group', 'By Blood Group'),
            ('marital_status', 'By Marital Status'),
        ],
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'})
    )
    
    include_charts = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_tables = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )



class PatientCensusForm(forms.Form):
    CENSUS_TYPES = (
        ('all', 'All Patients'),
        ('active', 'Active Only'),
        ('discharged', 'Discharged Only'),
    )
    
    GROUP_BY_CHOICES = (
        ('status', 'By Status'),
        ('gender', 'By Gender'),
        ('age_group', 'By Age Group'),
        ('daily', 'Daily Trend'),
    )
    
    census_type = forms.ChoiceField(choices=CENSUS_TYPES, required=False, 
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    group_by = forms.ChoiceField(choices=GROUP_BY_CHOICES, required=True,
                                widget=forms.Select(attrs={'class': 'form-control'}))
    

class DiagnosisFrequencyForm(forms.Form):
    """Form for diagnosis frequency report"""
    DIAGNOSIS_SCOPE = [
        ('all', 'All Diagnoses'),
        ('primary', 'Primary Diagnoses Only'),
        ('top_10', 'Top 10 Diagnoses'),
        ('top_20', 'Top 20 Diagnoses'),
    ]
    
    scope = forms.ChoiceField(
        choices=DIAGNOSIS_SCOPE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_icd10 = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    min_occurrences = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class PrescriptionAnalysisForm(forms.Form):
    """Form for prescription analysis"""
    ANALYSIS_TYPE = [
        ('most_prescribed', 'Most Prescribed Medications'),
        ('by_category', 'Prescriptions by Category'),
        ('cost_analysis', 'Cost Analysis'),
        ('refill_patterns', 'Refill Patterns'),
    ]
    
    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    medication_category = forms.ChoiceField(
        choices=[
            ('', 'All Categories'),
            ('antibiotics', 'Antibiotics'),
            ('pain_management', 'Pain Management'),
            ('cardiovascular', 'Cardiovascular'),
            ('diabetes', 'Diabetes'),
            ('mental_health', 'Mental Health'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class LabUtilizationForm(forms.Form):
    """Form for lab utilization report"""
    REPORT_SCOPE = [
        ('tests_ordered', 'Tests Ordered'),
        ('tests_completed', 'Tests Completed'),
        ('turnaround_time', 'Turnaround Time Analysis'),
        ('abnormal_results', 'Abnormal Results'),
    ]
    
    scope = forms.ChoiceField(
        choices=REPORT_SCOPE,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    test_category = forms.ChoiceField(
        choices=[
            ('', 'All Tests'),
            ('hematology', 'Hematology'),
            ('chemistry', 'Chemistry'),
            ('microbiology', 'Microbiology'),
            ('immunology', 'Immunology'),
            ('pathology', 'Pathology'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class ScheduledReportForm(forms.ModelForm):
    """Form for scheduling reports"""
    class Meta:
        model = ScheduledReport
        fields = ['name', 'report_type', 'format', 'frequency', 'day_of_week', 
                  'day_of_month', 'time', 'parameters', 'email_recipients', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'parameters': forms.HiddenInput(),
            'email_recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                                      'placeholder': 'Enter email addresses separated by commas'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_email_recipients(self):
        recipients = self.cleaned_data['email_recipients']
        if isinstance(recipients, str):
            # Split by commas and clean
            email_list = [email.strip() for email in recipients.split(',') if email.strip()]
            return email_list
        return recipients

class DashboardWidgetForm(forms.ModelForm):
    """Form for dashboard widgets"""
    class Meta:
        model = DashboardWidget
        fields = ['name', 'widget_type', 'chart_type', 'report_type', 
                  'data_config', 'width', 'height', 'refresh_interval']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'chart_type': forms.Select(attrs={'class': 'form-select'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'data_config': forms.HiddenInput(),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': 100}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }