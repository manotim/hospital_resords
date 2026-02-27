from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class ReportTemplate(models.Model):
    """Store predefined report templates"""
    REPORT_CATEGORIES = (
        ('clinical', 'Clinical Reports'),
        ('administrative', 'Administrative Reports'),
        ('financial', 'Financial Reports'),
        ('operational', 'Operational Reports'),
        ('statistical', 'Statistical Reports'),
    )
    
    REPORT_TYPES = (
        ('patient_census', 'Patient Census'),
        ('admission_discharge', 'Admission & Discharge Summary'),
        ('diagnosis_frequency', 'Diagnosis Frequency'),
        ('prescription_analysis', 'Prescription Analysis'),
        ('lab_utilization', 'Lab Utilization'),
        ('imaging_utilization', 'Imaging Utilization'),
        ('patient_demographics', 'Patient Demographics'),
        ('length_of_stay', 'Length of Stay Analysis'),
        ('readmission_rate', 'Readmission Rate'),
        ('mortality_rate', 'Mortality Rate'),
        ('physician_workload', 'Physician Workload'),
        ('department_performance', 'Department Performance'),
        ('custom', 'Custom Report'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=REPORT_CATEGORIES)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    template_config = models.JSONField(default=dict, help_text="JSON configuration for report template")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"

class GeneratedReport(models.Model):
    """Store generated reports"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=ReportTemplate.REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Date range for the report
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Report parameters stored as JSON
    parameters = models.JSONField(default=dict, blank=True)
    
    # Report data and file
    report_data = models.JSONField(default=dict, blank=True)
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # For scheduled reports
    is_scheduled = models.BooleanField(default=False)
    schedule_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"

class DashboardWidget(models.Model):
    """Configurable dashboard widgets for reports"""
    WIDGET_TYPES = (
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('metric', 'Metric'),
        ('list', 'List'),
    )
    
    CHART_TYPES = (
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
    )
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, null=True, blank=True)
    
    # Data source configuration
    report_type = models.CharField(max_length=50, choices=ReportTemplate.REPORT_TYPES)
    data_config = models.JSONField(default=dict, help_text="JSON configuration for data query")
    
    # Display settings
    width = models.IntegerField(default=6, help_text="Bootstrap column width (1-12)")
    height = models.IntegerField(default=300, help_text="Height in pixels")
    refresh_interval = models.IntegerField(default=0, help_text="Refresh interval in minutes (0 = no refresh)")
    
    # Position
    row_order = models.IntegerField(default=0)
    column_order = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['row_order', 'column_order']
    
    def __str__(self):
        return self.name

class ScheduledReport(models.Model):
    """Schedule reports to be generated automatically"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=ReportTemplate.REPORT_TYPES)
    format = models.CharField(max_length=10, choices=GeneratedReport.FORMAT_CHOICES, default='pdf')
    
    # Schedule configuration
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, null=True, blank=True)
    day_of_month = models.IntegerField(null=True, blank=True)
    time = models.TimeField(default='08:00')
    
    # Report parameters
    parameters = models.JSONField(default=dict)
    
    # Email recipients
    email_recipients = models.JSONField(default=list, help_text="List of email addresses")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"