from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.report_dashboard, name='dashboard'),
    
    # Report Generation
    path('generate/', views.generate_report, name='generate_report'),
    path('view/<int:pk>/', views.view_report, name='view_report'),
    path('download/<int:pk>/', views.download_report, name='download_report'),
    
    path('diagnosis-frequency/download/', views.diagnosis_frequency_report_download, name='diagnosis_frequency_download'),
    path('prescription-analysis/download/', views.prescription_analysis_report_download, name='prescription_analysis_download'),
    path('lab-utilization/download/', views.lab_utilization_report_download, name='lab_utilization_download'),

    
    # Specific Reports
    path('patient-census/', views.patient_census_report, name='patient_census'),
    path('diagnosis-frequency/', views.diagnosis_frequency_report, name='diagnosis_frequency'),
    path('prescription-analysis/', views.prescription_analysis_report, name='prescription_analysis'),
    path('lab-utilization/', views.lab_utilization_report, name='lab_utilization'),
    
    # Scheduled Reports
    path('scheduled/', views.scheduled_reports, name='scheduled_reports'),
    path('scheduled/create/', views.create_schedule, name='create_schedule'),
    path('scheduled/<int:pk>/edit/', views.edit_schedule, name='edit_schedule'),
    path('scheduled/<int:pk>/delete/', views.delete_schedule, name='delete_schedule'),
    
    # API Endpoints
    path('api/data/<str:report_type>/', views.api_report_data, name='api_report_data'),
    path('api/save-widget/', views.api_save_widget, name='api_save_widget'),

    path('medical-records/download/', views.medical_records_report_download, name='medical_records_download'),
    path('diagnosis-frequency/download/', views.diagnosis_frequency_report_download, name='diagnosis_frequency_download'),
    path('prescription-analysis/download/', views.prescription_analysis_report_download, name='prescription_analysis_download'),
    path('lab-utilization/download/', views.lab_utilization_report_download, name='lab_utilization_download'),
    path('imaging-utilization/download/', views.imaging_utilization_report_download, name='imaging_utilization_download'),
    path('procedure-analysis/download/', views.procedure_analysis_report_download, name='procedure_analysis_download'),
    path('patient-visit-summary/download/', views.patient_visit_summary_report_download, name='patient_visit_summary_download'),
]