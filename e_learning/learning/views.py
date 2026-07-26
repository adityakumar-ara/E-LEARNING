from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from django import forms
from .models import *

def home(request):
    videos = ELVideo.objects.all()
    context = {
        'videos': videos,
    }
    return render(request, 'home.html', context)

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Confirm Password")

    class Meta:
        model = CustomeUser
        fields = ['full_name', 'email', 'phone', 'gender', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your mobile number'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomeUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if CustomeUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("An account with this phone number already exists.")
        return phone

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True, label="Enter OTP", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit code'}))

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name or user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = LoginForm()
        
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')

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
    return render(request, 'register.html', {'form': form})

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
                user.gender = user_data.get('gender')
                user.save()

                messages.success(request, 'Welcome! Your account has been created successfully.')
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'registration/verify_otp.html', {'form': form})
