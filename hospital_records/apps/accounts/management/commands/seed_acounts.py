from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
import random

class Command(BaseCommand):
    help = 'Seed database with sample users'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding accounts data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@hospital.com',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            admin.profile.user_type = 'admin'
            admin.profile.department = 'Administration'
            admin.profile.phone_number = '+1234567890'
            admin.profile.address = '123 Hospital Main Street'
            admin.profile.save()
            self.stdout.write('Created admin user')
        
        # Create doctors
        doctors_data = [
            {'username': 'dr.smith', 'first_name': 'John', 'last_name': 'Smith', 'dept': 'Cardiology'},
            {'username': 'dr.jones', 'first_name': 'Sarah', 'last_name': 'Jones', 'dept': 'Pediatrics'},
            {'username': 'dr.williams', 'first_name': 'Michael', 'last_name': 'Williams', 'dept': 'Orthopedics'},
            {'username': 'dr.brown', 'first_name': 'Emily', 'last_name': 'Brown', 'dept': 'Neurology'},
        ]
        
        for doc_data in doctors_data:
            if not User.objects.filter(username=doc_data['username']).exists():
                doctor = User.objects.create_user(
                    username=doc_data['username'],
                    email=f"{doc_data['username']}@hospital.com",
                    password='doctor123',
                    first_name=doc_data['first_name'],
                    last_name=doc_data['last_name']
                )
                doctor.profile.user_type = 'doctor'
                doctor.profile.department = doc_data['dept']
                doctor.profile.phone_number = f"+1{random.randint(1000000000, 9999999999)}"
                doctor.profile.address = f"{random.randint(100, 999)} Medical Plaza"
                doctor.profile.save()
                self.stdout.write(f"Created doctor: {doc_data['username']}")
        
        # Create nurses
        nurses_data = [
            {'username': 'nurse.clark', 'first_name': 'Linda', 'last_name': 'Clark'},
            {'username': 'nurse.martin', 'first_name': 'Robert', 'last_name': 'Martin'},
        ]
        
        for nurse_data in nurses_data:
            if not User.objects.filter(username=nurse_data['username']).exists():
                nurse = User.objects.create_user(
                    username=nurse_data['username'],
                    email=f"{nurse_data['username']}@hospital.com",
                    password='nurse123',
                    first_name=nurse_data['first_name'],
                    last_name=nurse_data['last_name']
                )
                nurse.profile.user_type = 'nurse'
                nurse.profile.department = 'General Care'
                nurse.profile.phone_number = f"+1{random.randint(1000000000, 9999999999)}"
                nurse.profile.address = f"{random.randint(100, 999)} Healthcare Avenue"
                nurse.profile.save()
                self.stdout.write(f"Created nurse: {nurse_data['username']}")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded accounts data'))