from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator
from datetime import date


class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    MARITAL_STATUS = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )
    
    # Validators
    phone_regex = RegexValidator(
    regex=r'^[\d\+\-\(\)\s]+$',  # Allows digits, +, -, (), and spaces
    message="Enter a valid phone number (digits, +, -, parentheses, and spaces allowed)."
)
    
    # Identification
    patient_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        help_text="Auto-generated patient ID"
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    date_of_birth = models.DateField(
        verbose_name="Date of Birth",
        help_text="Format: YYYY-MM-DD"
    )
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES,
        verbose_name="Gender"
    )
    blood_group = models.CharField(
        max_length=3, 
        choices=BLOOD_GROUP_CHOICES,
        verbose_name="Blood Group"
    )
    marital_status = models.CharField(
        max_length=10, 
        choices=MARITAL_STATUS, 
        default='single',
        verbose_name="Marital Status"
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=15,
        validators=[phone_regex],
        verbose_name="Phone Number",
        help_text="Format: +1234567890"
    )
    email = models.EmailField(
        blank=True, 
        null=True,
        validators=[EmailValidator()],
        verbose_name="Email Address"
    )
    address = models.TextField(verbose_name="Address")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State")
    zip_code = models.CharField(
        max_length=10,
        verbose_name="ZIP Code"
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=200,
        verbose_name="Emergency Contact Name"
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        verbose_name="Emergency Contact Phone"
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        verbose_name="Relation to Patient"
    )
    
    # Medical Information
    primary_physician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='patients',
        verbose_name="Primary Physician"
    )
    allergies = models.TextField(
        blank=True,
        verbose_name="Allergies",
        help_text="List any known allergies"
    )
    chronic_conditions = models.TextField(
        blank=True,
        verbose_name="Chronic Conditions",
        help_text="List any chronic medical conditions"
    )
    current_medications = models.TextField(
        blank=True,
        verbose_name="Current Medications",
        help_text="List current medications and dosages"
    )
    
    # Insurance Information
    insurance_provider = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Insurance Provider"
    )
    insurance_policy_number = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Policy Number"
    )
    insurance_group_number = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Group Number"
    )
    
    # Status
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
        ('deceased', 'Deceased'),
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="Patient Status"
    )
    
    # Timestamps
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registration Date"
    )
    last_visit = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Last Visit Date"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )
    registered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='registered_patients',
        verbose_name="Registered By"
    )
    
    class Meta:
        ordering = ['-registration_date']
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]
        
    def __str__(self):
        return f"{self.patient_id} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def age(self):
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    def save(self, *args, **kwargs):
        if not self.patient_id:
            # Generate patient ID (e.g., P20240001)
            last_patient = Patient.objects.order_by('-id').first()
            if last_patient and last_patient.patient_id:
                try:
                    last_id = int(last_patient.patient_id[1:])
                    new_id = last_id + 1
                except (ValueError, IndexError):
                    new_id = 1
            else:
                new_id = 1
            self.patient_id = f"P{new_id:06d}"
        super().save(*args, **kwargs)


class Admission(models.Model):
    ADMISSION_TYPE = (
        ('emergency', 'Emergency'),
        ('routine', 'Routine'),
        ('transfer', 'Transfer'),
    )
    
    DISCHARGE_TYPE = (
        ('normal', 'Normal'),
        ('against_medical_advice', 'Against Medical Advice'),
        ('transfer', 'Transfer'),
        ('expired', 'Expired'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    admission_date = models.DateTimeField(auto_now_add=True)
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE)
    department = models.CharField(max_length=100)
    ward_number = models.CharField(max_length=20)
    bed_number = models.CharField(max_length=20)
    admitting_doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admissions')
    reason_for_admission = models.TextField()
    
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharge_type = models.CharField(max_length=30, choices=DISCHARGE_TYPE, null=True, blank=True)
    discharge_summary = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-admission_date']
    
    def __str__(self):
        return f"{self.patient.patient_id} - Admission {self.admission_date.date()}"

class VitalSign(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    respiratory_rate = models.IntegerField()
    oxygen_saturation = models.IntegerField()
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"Vitals for {self.patient.get_full_name()} at {self.recorded_at}"
    
    def save(self, *args, **kwargs):
        if self.height and self.weight:
            # Calculate BMI: weight(kg) / (height(m))^2
            height_m = float(self.height) / 100
            self.bmi = float(self.weight) / (height_m * height_m)
        super().save(*args, **kwargs)