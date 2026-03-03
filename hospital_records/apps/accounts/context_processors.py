# hospital_records/apps/accounts/context_processors.py
def user_role(request):
    """Add user role information to all templates"""
    context = {
        'is_authenticated': request.user.is_authenticated,
    }
    
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            user_type = request.user.profile.user_type
            context.update({
                'user_role': user_type,
                'is_admin': user_type == 'admin',
                'is_doctor': user_type == 'doctor',
                'is_nurse': user_type == 'nurse',
                'is_receptionist': user_type == 'receptionist',
                'is_lab_tech': user_type == 'lab_tech',
                'is_clinical_staff': user_type in ['doctor', 'nurse'],
                'is_medical_staff': user_type in ['doctor', 'nurse', 'lab_tech'],
            })
        else:
            # Default values if no profile
            context.update({
                'user_role': 'unknown',
                'is_admin': False,
                'is_doctor': False,
                'is_nurse': False,
                'is_receptionist': False,
                'is_lab_tech': False,
                'is_clinical_staff': False,
                'is_medical_staff': False,
            })
    
    return context