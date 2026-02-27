from django.db import models
from django.contrib.auth.models import User
from hospital_records.apps.patients.models import Patient
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

class MedicalRecord(models.Model):
    """Main medical record for patient visits"""
    RECORD_TYPES = (
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow Up'),
        ('emergency', 'Emergency'),
        ('routine_check', 'Routine Check'),
        ('pre_surgery', 'Pre-Surgery'),
        ('post_surgery', 'Post-Surgery'),
    )
    
    record_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='medical_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    visit_date = models.DateTimeField(auto_now_add=True)
    
    # Chief Complaint and History
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField()
    review_of_systems = models.TextField(blank=True)
    
    # Physical Examination
    physical_exam = models.TextField(blank=True)
    
    # Assessment and Plan
    assessment = models.TextField()
    plan = models.TextField()
    
    # Follow up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_instructions = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.record_number} - {self.patient.get_full_name()} - {self.visit_date.date()}"
    
    def save(self, *args, **kwargs):
        if not self.record_number:
            # Generate record number (e.g., MR20240001)
            last_record = MedicalRecord.objects.order_by('-id').first()
            if last_record:
                last_id = int(last_record.record_number[2:]) if last_record.record_number.startswith('MR') else 0
                new_id = last_id + 1
            else:
                new_id = 1
            self.record_number = f"MR{new_id:06d}"
        super().save(*args, **kwargs)

class Diagnosis(models.Model):
    """Patient diagnoses (ICD-10 codes)"""
    DIAGNOSIS_STATUS = (
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('chronic', 'Chronic'),
        ('rule_out', 'Rule Out'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='diagnoses')
    icd10_code = models.CharField(max_length=10)
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=DIAGNOSIS_STATUS, default='active')
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.icd10_code} - {self.description[:50]}"

class Prescription(models.Model):
    """Medication prescriptions"""
    MEDICATION_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('on_hold', 'On Hold'),
    )
    
    MEDICATION_UNITS = (
        ('mg', 'mg'),
        ('mcg', 'mcg'),
        ('g', 'g'),
        ('ml', 'ml'),
        ('tablet', 'tablet(s)'),
        ('capsule', 'capsule(s)'),
        ('puff', 'puff(s)'),
        ('drop', 'drop(s)'),
    )
    
    MEDICATION_FREQUENCY = (
        ('once', 'Once'),
        ('bid', 'Twice Daily'),
        ('tid', 'Three Times Daily'),
        ('qid', 'Four Times Daily'),
        ('q4h', 'Every 4 hours'),
        ('q6h', 'Every 6 hours'),
        ('q8h', 'Every 8 hours'),
        ('q12h', 'Every 12 hours'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('prn', 'As Needed'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=200)
    dosage = models.DecimalField(max_digits=10, decimal_places=2)
    dosage_unit = models.CharField(max_length=20, choices=MEDICATION_UNITS)
    frequency = models.CharField(max_length=20, choices=MEDICATION_FREQUENCY)
    route = models.CharField(max_length=50)  # Oral, IV, Topical, etc.
    duration = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField()
    refills = models.IntegerField(default=0)
    instructions = models.TextField()
    status = models.CharField(max_length=20, choices=MEDICATION_STATUS, default='active')
    prescribed_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-prescribed_date']
    
    def __str__(self):
        return f"{self.medication_name} - {self.dosage}{self.dosage_unit}"

class LabOrder(models.Model):
    """Laboratory test orders"""
    LAB_STATUS = (
        ('ordered', 'Ordered'),
        ('collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    LAB_PRIORITY = (
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='lab_orders')
    test_name = models.CharField(max_length=200)
    test_code = models.CharField(max_length=50)
    priority = models.CharField(max_length=20, choices=LAB_PRIORITY, default='routine')
    status = models.CharField(max_length=20, choices=LAB_STATUS, default='ordered')
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lab_orders')
    ordered_date = models.DateTimeField(auto_now_add=True)
    collected_date = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_samples')
    specimen_type = models.CharField(max_length=100, blank=True)
    clinical_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.test_name} - {self.get_status_display()}"

class LabResult(models.Model):
    """Laboratory test results"""
    lab_order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='result')
    result_value = models.CharField(max_length=200)
    reference_range = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)
    is_abnormal = models.BooleanField(default=False)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_tests')
    performed_date = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_tests')
    verified_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    result_file = models.FileField(upload_to='lab_results/', null=True, blank=True)
    
    def __str__(self):
        return f"Result for {self.lab_order.test_name}: {self.result_value} {self.unit}"

class ImagingOrder(models.Model):
    """Radiology/Imaging orders"""
    IMAGING_STATUS = (
        ('ordered', 'Ordered'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    IMAGING_PRIORITY = (
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    )
    
    IMAGING_TYPE = (
        ('xray', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('mammogram', 'Mammogram'),
        ('pet', 'PET Scan'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='imaging_orders')
    imaging_type = models.CharField(max_length=20, choices=IMAGING_TYPE)
    body_part = models.CharField(max_length=100)
    clinical_history = models.TextField()
    priority = models.CharField(max_length=20, choices=IMAGING_PRIORITY, default='routine')
    status = models.CharField(max_length=20, choices=IMAGING_STATUS, default='ordered')
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='imaging_orders')
    ordered_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_imaging_type_display()} - {self.body_part}"

class ImagingResult(models.Model):
    """Imaging study results"""
    imaging_order = models.OneToOneField(ImagingOrder, on_delete=models.CASCADE, related_name='result')
    findings = models.TextField()
    impression = models.TextField()
    radiologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='radiology_reports')
    report_date = models.DateTimeField(auto_now_add=True)
    image_file = models.FileField(upload_to='imaging/', null=True, blank=True)
    report_file = models.FileField(upload_to='imaging_reports/', null=True, blank=True)
    
    def __str__(self):
        return f"Report for {self.imaging_order}"

class Procedure(models.Model):
    """Medical procedures performed"""
    PROCEDURE_STATUS = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='procedures')
    procedure_name = models.CharField(max_length=200)
    procedure_code = models.CharField(max_length=20)  # CPT code
    date_performed = models.DateTimeField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_procedures')
    assisted_by = models.ManyToManyField(User, blank=True, related_name='assisted_procedures')
    location = models.CharField(max_length=100)
    findings = models.TextField()
    complications = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PROCEDURE_STATUS, default='scheduled')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.procedure_name} - {self.date_performed.date()}"

class ClinicalNote(models.Model):
    """Additional clinical notes and observations"""
    NOTE_TYPES = (
        ('progress', 'Progress Note'),
        ('nursing', 'Nursing Note'),
        ('consult', 'Consultation Note'),
        ('discharge', 'Discharge Summary'),
        ('transfer', 'Transfer Note'),
    )
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='clinical_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=False)  # For sensitive notes
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_note_type_display()} by {self.author.get_full_name()} - {self.created_at.date()}"