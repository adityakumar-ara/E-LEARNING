from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import RegistrationForm, OTPVerificationForm
from .models import CustomeUser

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            otp = random.randint(100000, 999999)
            user_data = form.cleaned_data
            
            subject = 'Your Email Verification OTP'
            message = f'Hello {user_data["full_name"]},\n\nYour OTP for registration is: {otp}\n\nThank you!'
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')
            to_email = [user_data['email']]
            
            try:
                send_mail(subject, message, from_email, to_email)
                request.session['registration_data'] = user_data
                request.session['otp'] = otp
                messages.success(request, 'An OTP has been sent to your email. Please verify to complete registration.')
                return redirect('verify_otp')
            except Exception as e:
                messages.error(request, f'Failed to send OTP email. Please check your email settings. Error: {e}')

    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('home')
    if 'registration_data' not in request.session or 'otp' not in request.session:
        messages.error(request, 'Session expired or invalid request. Please register again.')
        return redirect('register')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] == str(request.session.get('otp')):
                user_data = request.session.pop('registration_data')
                request.session.pop('otp')
                
                user = CustomeUser.objects.create_user(
                    username=user_data['email'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.full_name = user_data['full_name']
                user.phone = user_data['phone']
                user.save()

                messages.success(request, 'Welcome! Your account has been created successfully.')
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'registration/verify_otp.html', {'form': form})
