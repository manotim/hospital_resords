# hospital_records/apps/accounts/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin for class-based views to restrict by role"""
    allowed_roles = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'profile'):
            return False
        
        user_type = self.request.user.profile.user_type
        
        # Superusers and admins can access everything
        if self.request.user.is_superuser or user_type == 'admin':
            return True
        
        return user_type in self.allowed_roles
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('patients:dashboard')

class DoctorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['doctor']

class NurseRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['nurse']

class ClinicalStaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['doctor', 'nurse']

class ReceptionistRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['receptionist']

class LabTechRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['lab_tech']