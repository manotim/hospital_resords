from django.contrib import admin
from .models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)

class DiagnosisInline(admin.TabularInline):
    model = Diagnosis
    extra = 1

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1

class LabOrderInline(admin.TabularInline):
    model = LabOrder
    extra = 0

class ImagingOrderInline(admin.TabularInline):
    model = ImagingOrder
    extra = 0

class ProcedureInline(admin.TabularInline):
    model = Procedure
    extra = 0

class ClinicalNoteInline(admin.TabularInline):
    model = ClinicalNote
    extra = 0

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['record_number', 'patient', 'doctor', 'record_type', 'visit_date', 'is_active']
    list_filter = ['record_type', 'is_active', 'visit_date']
    search_fields = ['record_number', 'patient__first_name', 'patient__last_name', 'patient__patient_id']
    readonly_fields = ['record_number', 'created_at', 'updated_at']
    inlines = [DiagnosisInline, PrescriptionInline, LabOrderInline, ImagingOrderInline, ProcedureInline, ClinicalNoteInline]
    
    fieldsets = (
        ('Record Information', {
            'fields': ('record_number', 'patient', 'doctor', 'record_type', 'visit_date', 'is_active')
        }),
        ('Chief Complaint and History', {
            'fields': ('chief_complaint', 'history_of_present_illness', 'review_of_systems')
        }),
        ('Examination', {
            'fields': ('physical_exam',)
        }),
        ('Assessment and Plan', {
            'fields': ('assessment', 'plan')
        }),
        ('Follow-up', {
            'fields': ('follow_up_date', 'follow_up_instructions')
        }),
    )

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['medication_name', 'medical_record', 'dosage', 'dosage_unit', 'frequency', 'status']
    list_filter = ['status', 'frequency', 'route']
    search_fields = ['medication_name', 'medical_record__patient__first_name', 'medical_record__patient__last_name']

@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ['test_name', 'medical_record', 'priority', 'status', 'ordered_date']
    list_filter = ['status', 'priority', 'ordered_date']
    search_fields = ['test_name', 'medical_record__patient__first_name', 'medical_record__patient__last_name']

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ['lab_order', 'result_value', 'is_abnormal', 'performed_date', 'verified_date']
    list_filter = ['is_abnormal', 'performed_date']
    search_fields = ['lab_order__test_name']

@admin.register(ImagingOrder)
class ImagingOrderAdmin(admin.ModelAdmin):
    list_display = ['imaging_type', 'body_part', 'medical_record', 'priority', 'status', 'ordered_date']
    list_filter = ['status', 'priority', 'imaging_type']
    search_fields = ['body_part', 'medical_record__patient__first_name', 'medical_record__patient__last_name']

@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ['procedure_name', 'medical_record', 'performed_by', 'date_performed', 'status']
    list_filter = ['status', 'date_performed']
    search_fields = ['procedure_name', 'procedure_code']

@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ['note_type', 'author', 'medical_record', 'created_at', 'is_private']
    list_filter = ['note_type', 'is_private', 'created_at']
    search_fields = ['content']