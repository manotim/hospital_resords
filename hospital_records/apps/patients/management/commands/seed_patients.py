from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.patients.models import Patient, Admission, VitalSign
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Seed database with sample patients'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding patients data...')
        
        # Get doctors for assignments
        doctors = User.objects.filter(profile__user_type='doctor')
        if not doctors.exists():
            self.stdout.write(self.style.WARNING('No doctors found. Please seed accounts first.'))
            return
        
        # Sample patient data
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Lisa', 'Robert', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA']
        
        # Create 50 sample patients
        for i in range(50):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Generate random date of birth (18-80 years old)
            days_old = random.randint(18*365, 80*365)
            dob = datetime.now() - timedelta(days=days_old)
            
            # Generate random registration date (last 2 years)
            reg_days = random.randint(0, 730)
            reg_date = datetime.now() - timedelta(days=reg_days)
            
            status = random.choice(['active', 'discharged', 'transferred'])
            
            # Create patient
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob.date(),
                gender=random.choice(['M', 'F']),
                blood_group=random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
                marital_status=random.choice(['single', 'married', 'divorced', 'widowed']),
                phone_number=f"+1{random.randint(1000000000, 9999999999)}",
                email=f"{first_name.lower()}.{last_name.lower()}@email.com",
                address=f"{random.randint(100, 999)} Main Street",
                city=random.choice(cities),
                state=random.choice(states),
                zip_code=f"{random.randint(10000, 99999)}",
                emergency_contact_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                emergency_contact_phone=f"+1{random.randint(1000000000, 9999999999)}",
                emergency_contact_relation=random.choice(['Spouse', 'Parent', 'Child', 'Sibling']),
                primary_physician=random.choice(doctors),
                allergies=random.choice(['Penicillin', 'Pollen', 'Latex', 'Sulfa', 'None', 'None', 'None']),
                chronic_conditions=random.choice(['Hypertension', 'Diabetes', 'Asthma', 'None', 'None']),
                current_medications=random.choice(['Lisinopril', 'Metformin', 'Albuterol', 'None', 'None']),
                insurance_provider=random.choice(['Blue Cross', 'Aetna', 'Cigna', 'UnitedHealth', 'None']),
                insurance_policy_number=f"POL{random.randint(10000, 99999)}",
                insurance_group_number=f"GRP{random.randint(10000, 99999)}",
                status=status,
                registration_date=reg_date,
                registered_by=random.choice(doctors),
            )
            
            # Create admissions
            num_admissions = random.randint(0, 3)
            for j in range(num_admissions):
                admission_date = reg_date + timedelta(days=random.randint(1, 365))
                is_active = (j == num_admissions - 1 and status == 'active')
                
                admission = Admission.objects.create(
                    patient=patient,
                    admission_date=admission_date,
                    admission_type=random.choice(['emergency', 'routine']),
                    department=random.choice(['Cardiology', 'Pediatrics', 'Orthopedics', 'Neurology', 'General']),
                    ward_number=f"W{random.randint(1, 5)}",
                    bed_number=f"B{random.randint(1, 20)}",
                    admitting_doctor=random.choice(doctors),
                    reason_for_admission=random.choice([
                        'Chest pain', 'Difficulty breathing', 'Fever', 'Accident', 'Surgery'
                    ]),
                    is_active=is_active
                )
                
                if not is_active:
                    discharge_date = admission_date + timedelta(days=random.randint(1, 10))
                    admission.discharge_date = discharge_date
                    admission.discharge_type = random.choice(['normal', 'against_medical_advice'])
                    admission.discharge_summary = f"Patient discharged after {random.randint(1, 10)} days of treatment."
                    admission.save()
            
            # Create vital signs
            num_vitals = random.randint(0, 10)
            for k in range(num_vitals):
                vital_date = reg_date + timedelta(days=random.randint(0, 365))
                VitalSign.objects.create(
                    patient=patient,
                    recorded_by=random.choice(doctors),
                    recorded_at=vital_date,
                    blood_pressure_systolic=random.randint(100, 160),
                    blood_pressure_diastolic=random.randint(60, 100),
                    heart_rate=random.randint(60, 100),
                    temperature=round(random.uniform(97.0, 99.5), 1),
                    respiratory_rate=random.randint(12, 20),
                    oxygen_saturation=random.randint(95, 100),
                    height=random.randint(150, 190),
                    weight=random.uniform(50, 100),
                    notes="Routine checkup"
                )
            
            if i % 10 == 0:
                self.stdout.write(f"Created {i} patients...")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded 50 patients'))