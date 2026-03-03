# hospital_records/apps/patients/urls.py
from django.urls import path
from . import views, views_dashboards

app_name = 'patients'

urlpatterns = [
    # Role-specific dashboards
    path('dashboard/doctor/', views_dashboards.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/nurse/', views_dashboards.nurse_dashboard, name='nurse_dashboard'),
    path('dashboard/reception/', views_dashboards.reception_dashboard, name='reception_dashboard'),
    path('dashboard/lab/', views_dashboards.lab_dashboard, name='lab_dashboard'),
    
    # Main dashboard (redirects based on role)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Patient management
    path('', views.patient_list, name='patient_list'),
    path('add/', views.patient_add, name='patient_add'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    
    # Clinical actions
    path('<int:pk>/admit/', views.admit_patient, name='admit_patient'),
    path('<int:pk>/discharge/', views.discharge_patient, name='discharge_patient'),
    path('<int:pk>/vitals/add/', views.add_vitals, name='add_vitals'),
]