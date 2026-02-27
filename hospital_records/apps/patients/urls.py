# patients/urls.py
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('list/', views.patient_list, name='patient_list'),
    path('add/', views.patient_add, name='patient_add'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('<int:pk>/admit/', views.admit_patient, name='admit_patient'),
    path('<int:pk>/discharge/', views.discharge_patient, name='discharge_patient'),
    path('<int:pk>/vitals/add/', views.add_vitals, name='add_vitals'),
    path('api/patients/', views.api_patients, name='api_patients'),
]