from django.contrib import admin
from .models import Patient, Admission, VitalSign

class AdmissionInline(admin.TabularInline):
    model = Admission
    extra = 0
    readonly_fields = ['admission_date', 'discharge_date']

class VitalSignInline(admin.TabularInline):
    model = VitalSign
    extra = 0
    readonly_fields = ['recorded_at']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'first_name', 'last_name', 'gender', 'blood_group', 'status', 'registration_date']
    list_filter = ['status', 'gender', 'blood_group', 'marital_status']
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone_number', 'email']
    readonly_fields = ['patient_id', 'registration_date', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group', 'marital_status')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'address', 'city', 'state', 'zip_code')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')
        }),
        ('Medical Information', {
            'fields': ('primary_physician', 'allergies', 'chronic_conditions', 'current_medications')
        }),
        ('Insurance', {
            'fields': ('insurance_provider', 'insurance_policy_number', 'insurance_group_number')
        }),
        ('Status', {
            'fields': ('status', 'last_visit', 'registered_by')
        }),
    )
    inlines = [AdmissionInline, VitalSignInline]

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'admission_date', 'department', 'ward_number', 'bed_number', 'is_active']
    list_filter = ['is_active', 'admission_type', 'department']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__patient_id']
    readonly_fields = ['admission_date']

@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ['patient', 'recorded_at', 'recorded_by', 'blood_pressure_systolic', 'heart_rate', 'temperature']
    list_filter = ['recorded_at']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['recorded_at', 'bmi']