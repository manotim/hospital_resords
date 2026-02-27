from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    # Medical Records
    path('', views.record_list, name='record_list'),
    path('create/<int:patient_id>/', views.create_medical_record, name='create_record'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
    path('<int:pk>/edit/', views.edit_record, name='edit_record'),
    path('<int:pk>/print/', views.print_record, name='print_record'),
    
    # Prescriptions
    path('prescription/add/<int:record_id>/', views.add_prescription, name='add_prescription'),
    path('prescription/<int:pk>/edit/', views.edit_prescription, name='edit_prescription'),
    path('prescription/<int:pk>/delete/', views.delete_prescription, name='delete_prescription'),
    
    # Lab Orders and Results
    path('lab/order/<int:record_id>/', views.order_lab, name='order_lab'),
    path('lab/<int:pk>/', views.lab_detail, name='lab_detail'),
    path('lab/<int:pk>/add-result/', views.add_lab_result, name='add_lab_result'),
    path('lab/<int:pk>/verify/', views.verify_lab_result, name='verify_lab_result'),
    
    # Imaging Orders and Results
    path('imaging/order/<int:record_id>/', views.order_imaging, name='order_imaging'),
    path('imaging/<int:pk>/', views.imaging_detail, name='imaging_detail'),
    path('imaging/<int:pk>/add-result/', views.add_imaging_result, name='add_imaging_result'),
    
    # Procedures
    path('procedure/add/<int:record_id>/', views.add_procedure, name='add_procedure'),
    path('procedure/<int:pk>/edit/', views.edit_procedure, name='edit_procedure'),
    
    # Clinical Notes
    path('note/add/<int:record_id>/', views.add_clinical_note, name='add_clinical_note'),
    path('note/<int:pk>/edit/', views.edit_clinical_note, name='edit_clinical_note'),

    path('api/recent-records/', views.api_recent_records, name='api_recent_records'),
    path('api/quick-create-record/', views.api_quick_create_record, name='api_quick_create_record'),
]