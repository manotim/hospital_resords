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
    """Form for generating reports with title selection"""
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
    
    # Predefined titles for each report type
    TITLE_CHOICES = {
        'patient_census': [
            ('Patient Census Report', 'Patient Census Report'),
            ('Monthly Patient Census', 'Monthly Patient Census'),
            ('Department-wise Patient Census', 'Department-wise Patient Census'),
            ('Custom Title', 'Custom Title...'),
        ],
        'admission_discharge': [
            ('Admission & Discharge Summary', 'Admission & Discharge Summary'),
            ('Daily Admission Report', 'Daily Admission Report'),
            ('Discharge Analysis', 'Discharge Analysis'),
            ('Custom Title', 'Custom Title...'),
        ],
        'diagnosis_frequency': [
            ('Diagnosis Frequency Report', 'Diagnosis Frequency Report'),
            ('Top 10 Diagnoses', 'Top 10 Diagnoses'),
            ('ICD-10 Code Analysis', 'ICD-10 Code Analysis'),
            ('Custom Title', 'Custom Title...'),
        ],
        'prescription_analysis': [
            ('Prescription Analysis', 'Prescription Analysis'),
            ('Most Prescribed Medications', 'Most Prescribed Medications'),
            ('Medication Usage Report', 'Medication Usage Report'),
            ('Custom Title', 'Custom Title...'),
        ],
        'lab_utilization': [
            ('Lab Utilization Report', 'Lab Utilization Report'),
            ('Lab Test Statistics', 'Lab Test Statistics'),
            ('Abnormal Results Report', 'Abnormal Results Report'),
            ('Custom Title', 'Custom Title...'),
        ],
        'imaging_utilization': [
            ('Imaging Utilization Report', 'Imaging Utilization Report'),
            ('Radiology Department Report', 'Radiology Department Report'),
            ('Imaging Statistics', 'Imaging Statistics'),
            ('Custom Title', 'Custom Title...'),
        ],
        'patient_demographics': [
            ('Patient Demographics Report', 'Patient Demographics Report'),
            ('Age & Gender Distribution', 'Age & Gender Distribution'),
            ('Patient Population Analysis', 'Patient Population Analysis'),
            ('Custom Title', 'Custom Title...'),
        ],
        'length_of_stay': [
            ('Length of Stay Analysis', 'Length of Stay Analysis'),
            ('Average LOS Report', 'Average LOS Report'),
            ('Department LOS Comparison', 'Department LOS Comparison'),
            ('Custom Title', 'Custom Title...'),
        ],
        'readmission_rate': [
            ('Readmission Rate Report', 'Readmission Rate Report'),
            ('30-Day Readmission Analysis', '30-Day Readmission Analysis'),
            ('Readmission Risk Factors', 'Readmission Risk Factors'),
            ('Custom Title', 'Custom Title...'),
        ],
        'mortality_rate': [
            ('Mortality Rate Report', 'Mortality Rate Report'),
            ('Mortality Analysis', 'Mortality Analysis'),
            ('Outcome Statistics', 'Outcome Statistics'),
            ('Custom Title', 'Custom Title...'),
        ],
        'physician_workload': [
            ('Physician Workload Report', 'Physician Workload Report'),
            ('Doctor Productivity Analysis', 'Doctor Productivity Analysis'),
            ('Department Workload Distribution', 'Department Workload Distribution'),
            ('Custom Title', 'Custom Title...'),
        ],
        'department_performance': [
            ('Department Performance Report', 'Department Performance Report'),
            ('Department KPIs', 'Department KPIs'),
            ('Performance Metrics', 'Performance Metrics'),
            ('Custom Title', 'Custom Title...'),
        ],
    }
    
    report_type = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_report_type'})
    )
    
    title_option = forms.ChoiceField(
        choices=[('', '-- Select Title --')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_title_option'})
    )
    
    custom_title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter custom report title',
            'id': 'id_custom_title',
            'style': 'display: none;'
        })
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial title choices based on default report type
        if 'initial' not in kwargs:
            self.fields['title_option'].choices = self.get_title_choices('patient_census')
    
    def get_title_choices(self, report_type):
        """Get title choices for a specific report type"""
        choices = [('', '-- Select Title --')]
        if report_type in self.TITLE_CHOICES:
            choices.extend(self.TITLE_CHOICES[report_type])
        return choices
    
    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')
        title_option = cleaned_data.get('title_option')
        custom_title = cleaned_data.get('custom_title')
        
        # Set the actual title based on selection
        if title_option == 'Custom Title...':
            if not custom_title:
                self.add_error('custom_title', 'Please enter a custom title')
            else:
                cleaned_data['title'] = custom_title
        elif title_option:
            cleaned_data['title'] = title_option
        else:
            self.add_error('title_option', 'Please select a title')
        
        return cleaned_data


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