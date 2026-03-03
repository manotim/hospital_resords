from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
from .forms import UserProfileForm, UserForm

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user has profile
            if hasattr(user, 'profile'):
                user_type = user.profile.user_type
                
                # Role-based redirect
                if user_type == 'doctor':
                    return redirect('patients:doctor_dashboard')
                elif user_type == 'nurse':
                    return redirect('patients:nurse_dashboard')
                elif user_type == 'receptionist':
                    return redirect('patients:reception_dashboard')
                elif user_type == 'lab_tech':
                    return redirect('patients:lab_dashboard')
                elif user_type == 'admin':
                    return redirect('patients:dashboard')
            else:
                messages.warning(request, 'Please complete your profile.')
                return redirect('accounts:edit_profile')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@login_required
def profile(request):
    """User profile view"""
    context = {
        'user': request.user,
        # You can add more context data as needed
        'stats': {
            'total_patients': 0,  # Add your actual stats here
            'total_records': 0,
            'total_prescriptions': 0,
        },
        'recent_activity': [],  # Add recent activity here
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('accounts:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})