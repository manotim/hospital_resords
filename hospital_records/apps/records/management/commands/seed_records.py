from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.patients.models import Patient
from apps.records.models import (
    MedicalRecord, Diagnosis, Prescription, LabOrder, LabResult,
    ImagingOrder, ImagingResult, Procedure, ClinicalNote
)
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Seed database with sample medical records'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding medical records data...')
        
        # Get doctors and patients
        doctors = User.objects.filter(profile__user_type='doctor')
        patients = Patient.objects.all()
        
        if not doctors.exists() or not patients.exists():
            self.stdout.write(self.style.WARNING('Please seed accounts and patients first'))
            return
        
        # Sample data for records
        chief_complaints = [
            'Chest pain and shortness of breath',
            'Persistent headache for 3 days',
            'Fever and cough',
            'Lower back pain',
            'Abdominal pain',
            'Dizziness and fatigue',
            'Sore throat and fever',
            'Joint pain in knees',
            'Skin rash',
            'Nausea and vomiting'
        ]
        
        diagnoses_data = [
            ('I10', 'Essential hypertension'),
            ('J45', 'Asthma'),
            ('E11', 'Type 2 diabetes mellitus'),
            ('M54', 'Lower back pain'),
            ('J02', 'Acute pharyngitis'),
            ('N39', 'Urinary tract infection'),
            ('J18', 'Pneumonia'),
            ('I20', 'Angina pectoris'),
            ('K29', 'Gastritis'),
            ('M17', 'Osteoarthritis of knee')
        ]
        
        medications = [
            ('Lisinopril', '10', 'mg', 'daily', 'Oral'),
            ('Metformin', '500', 'mg', 'bid', 'Oral'),
            ('Albuterol', '2', 'puff', 'q4h', 'Inhalation'),
            ('Ibuprofen', '400', 'mg', 'tid', 'Oral'),
            ('Amoxicillin', '500', 'mg', 'bid', 'Oral'),
            ('Omeprazole', '20', 'mg', 'daily', 'Oral'),
            ('Levothyroxine', '50', 'mcg', 'daily', 'Oral'),
            ('Amlodipine', '5', 'mg', 'daily', 'Oral'),
            ('Metoprolol', '25', 'mg', 'bid', 'Oral'),
            ('Hydrochlorothiazide', '12.5', 'mg', 'daily', 'Oral')
        ]
        
        lab_tests = [
            ('CBC', 'Complete Blood Count'),
            ('BMP', 'Basic Metabolic Panel'),
            ('Lipid Panel', 'Lipid Profile'),
            ('HbA1c', 'Hemoglobin A1c'),
            ('TSH', 'Thyroid Stimulating Hormone'),
            ('UA', 'Urinalysis'),
            ('Blood Culture', 'Blood Culture'),
            ('Liver Panel', 'Liver Function Tests'),
            ('CK', 'Creatine Kinase'),
            ('Troponin', 'Troponin I')
        ]
        
        imaging_studies = [
            ('xray', 'Chest', 'Chest X-Ray'),
            ('xray', 'Knee', 'Knee X-Ray'),
            ('ct', 'Head', 'Head CT'),
            ('mri', 'Brain', 'Brain MRI'),
            ('ultrasound', 'Abdomen', 'Abdominal Ultrasound'),
            ('xray', 'Spine', 'Spine X-Ray'),
            ('mri', 'Knee', 'Knee MRI'),
            ('ct', 'Abdomen', 'Abdominal CT')
        ]
        
        # Create medical records for each patient
        records_created = 0
        for patient in patients:
            # Each patient has 1-5 medical records
            num_records = random.randint(1, 5)
            
            for i in range(num_records):
                # Random date within last year
                days_ago = random.randint(0, 365)
                visit_date = datetime.now() - timedelta(days=days_ago)
                
                # Select random doctor
                doctor = random.choice(doctors)
                
                # Create medical record
                record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=doctor,
                    record_type=random.choice(['consultation', 'follow_up', 'emergency', 'routine_check']),
                    visit_date=visit_date,
                    chief_complaint=random.choice(chief_complaints),
                    history_of_present_illness=f"Patient reports {random.choice(chief_complaints).lower()} for {random.randint(1, 7)} days.",
                    review_of_systems="Review of systems negative except as above.",
                    physical_exam="Vitals stable. Patient in no acute distress.",
                    assessment="Based on presentation and exam, likely diagnosis as discussed.",
                    plan=f"Will treat with appropriate medications. Follow up in {random.randint(1, 4)} weeks.",
                    follow_up_date=visit_date + timedelta(days=random.randint(14, 30)) if random.choice([True, False]) else None,
                    follow_up_instructions="Return sooner if symptoms worsen.",
                    is_active=random.choice([True, False])
                )
                
                # Add diagnoses (1-3 per record)
                num_diagnoses = random.randint(1, 3)
                selected_diagnoses = random.sample(diagnoses_data, num_diagnoses)
                for j, (code, desc) in enumerate(selected_diagnoses):
                    Diagnosis.objects.create(
                        medical_record=record,
                        icd10_code=code,
                        description=desc,
                        status=random.choice(['active', 'resolved', 'chronic']),
                        is_primary=(j == 0),
                        notes=f"Diagnosis notes for {desc}"
                    )
                
                # Add prescriptions (0-3 per record)
                num_prescriptions = random.randint(0, 3)
                if num_prescriptions > 0:
                    selected_meds = random.sample(medications, num_prescriptions)
                    for med_name, dosage, unit, freq, route in selected_meds:
                        Prescription.objects.create(
                            medical_record=record,
                            medication_name=med_name,
                            dosage=dosage,
                            dosage_unit=unit,
                            frequency=freq,
                            route=route,
                            duration=f"{random.randint(7, 30)} days",
                            quantity=random.randint(10, 60),
                            refills=random.randint(0, 3),
                            instructions=f"Take as directed. {random.choice(['With food', 'On empty stomach', 'At bedtime'])}.",
                            status=random.choice(['active', 'completed', 'discontinued']),
                            prescribed_date=visit_date
                        )
                
                # Add lab orders (0-2 per record)
                num_labs = random.randint(0, 2)
                if num_labs > 0:
                    selected_labs = random.sample(lab_tests, num_labs)
                    for test_code, test_name in selected_labs:
                        lab_order = LabOrder.objects.create(
                            medical_record=record,
                            test_name=test_name,
                            test_code=test_code,
                            priority=random.choice(['routine', 'urgent', 'stat']),
                            status=random.choice(['ordered', 'completed', 'in_progress']),
                            ordered_by=doctor,
                            ordered_date=visit_date,
                            specimen_type=random.choice(['Blood', 'Urine', 'Serum', 'Plasma']),
                            clinical_notes=f"Ordered for {test_name.lower()}"
                        )
                        
                        # Add result for some lab orders
                        if random.choice([True, False]):
                            LabResult.objects.create(
                                lab_order=lab_order,
                                result_value=str(random.randint(50, 200)),
                                reference_range="70-110" if test_code == 'BMP' else "4.0-5.6",
                                unit=random.choice(['mg/dL', 'g/dL', 'U/L']),
                                is_abnormal=random.choice([True, False]),
                                performed_by=random.choice(doctors),
                                performed_date=visit_date + timedelta(days=random.randint(1, 3)),
                                notes="Result verified and reported."
                            )
                            lab_order.status = 'completed'
                            lab_order.save()
                
                # Add imaging orders (0-1 per record)
                if random.choice([True, False]) and random.random() > 0.7:
                    img_type, body_part, description = random.choice(imaging_studies)
                    imaging_order = ImagingOrder.objects.create(
                        medical_record=record,
                        imaging_type=img_type,
                        body_part=body_part,
                        clinical_history=record.chief_complaint,
                        priority=random.choice(['routine', 'urgent']),
                        status=random.choice(['ordered', 'completed']),
                        ordered_by=doctor,
                        ordered_date=visit_date,
                        scheduled_date=visit_date + timedelta(days=random.randint(1, 7))
                    )
                    
                    # Add result for some imaging orders
                    if random.choice([True, False]):
                        ImagingResult.objects.create(
                            imaging_order=imaging_order,
                            findings="Normal study. No acute findings identified.",
                            impression="Normal examination.",
                            radiologist=random.choice(doctors),
                            report_date=visit_date + timedelta(days=random.randint(2, 5))
                        )
                        imaging_order.status = 'completed'
                        imaging_order.save()
                
                # Add clinical notes (0-2 per record)
                num_notes = random.randint(0, 2)
                for _ in range(num_notes):
                    ClinicalNote.objects.create(
                        medical_record=record,
                        note_type=random.choice(['progress', 'nursing', 'consult']),
                        author=random.choice(doctors),
                        content=f"Patient {random.choice(['improving', 'stable', 'requires monitoring'])}. "
                               f"Will continue current management. "
                               f"Follow up as scheduled.",
                        is_private=random.choice([True, False])
                    )
                
                records_created += 1
                
                if records_created % 20 == 0:
                    self.stdout.write(f"Created {records_created} medical records...")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {records_created} medical records'))