# hospital_records/apps/accounts/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden

def role_required(allowed_roles=[]):
    """Decorator to restrict access based on user roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            # Check if user has a profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found. Please contact administrator.')
                return redirect('accounts:profile')
            
            user_type = request.user.profile.user_type
            
            # Allow superusers and admins to access everything
            if request.user.is_superuser or user_type == 'admin':
                return view_func(request, *args, **kwargs)
            
            # Check if user's role is allowed
            if user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f'Access denied. You do not have permission to access this page.')
                raise PermissionDenied
        return _wrapped_view
    return decorator

def doctor_required(view_func):
    """Decorator for doctor-only views"""
    return role_required(['doctor'])(view_func)

def nurse_required(view_func):
    """Decorator for nurse-only views"""
    return role_required(['nurse'])(view_func)

def receptionist_required(view_func):
    """Decorator for receptionist-only views"""
    return role_required(['receptionist'])(view_func)

def lab_tech_required(view_func):
    """Decorator for lab technician-only views"""
    return role_required(['lab_tech'])(view_func)

def clinical_staff_required(view_func):
    """Decorator for clinical staff (doctors and nurses)"""
    return role_required(['doctor', 'nurse'])(view_func)

def medical_staff_required(view_func):
    """Decorator for medical staff (doctors, nurses, and lab techs)"""
    return role_required(['doctor', 'nurse', 'lab_tech'])(view_func)

def admin_required(view_func):
    """Decorator for admin-only views"""
    return role_required(['admin'])(view_func)

def multiple_roles_required(allowed_roles=[]):
    """Alias for role_required for backward compatibility"""
    return role_required(allowed_roles)