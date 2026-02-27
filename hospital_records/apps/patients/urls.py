# patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('patients/<int:pk>/admit/', views.admit_patient, name='admit_patient'),
    path('patients/<int:pk>/discharge/', views.discharge_patient, name='discharge_patient'),
    path('patients/<int:pk>/vitals/add/', views.add_vitals, name='add_vitals'),
]