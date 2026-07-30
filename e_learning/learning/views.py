from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.shortcuts import redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
from django.db.models import Count, Avg
from django import forms
from django.utils import timezone
from .models import *

def home(request):
    videos = ELVideo.objects.all()
    featured_courses = Courses.objects.filter(is_featured=True)
    upcoming_classes = ClassSchedule.objects.select_related('course').filter(
        start_time__gte=timezone.now()
    ).order_by('start_time')[:3]

    context = {
        'videos': videos,
        'feature_courses' : featured_courses,
        'upcoming_classes': upcoming_classes,
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
        
    return render(request, 'login.html', {'form': form})

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
    
    return render(request, 'verify_otp.html', {'form': form})

def course_view(request):
    query = request.GET.get('q', '')
    courses_list = Courses.objects.annotate(
        enrollment_count=Count('enrollments'),
        average_rating=Avg('reviews__rating')
    ).select_related('instructor').order_by('-is_featured', 'course_name')

    if query:
        courses_list = courses_list.filter(course_name__icontains=query)

    context = {
        'courses': courses_list,
        'search_query': query,
    }
    return render(request, 'courses_list.html', context)

def course_detail(request, course_id):
    """
    Displays the details for a specific course, including upcoming live classes.
    """
    course = get_object_or_404(Courses, id=course_id)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()

    # Get live and upcoming schedules
    now = timezone.now()
    live_schedules = course.class_schedules.filter(start_time__lte=now, end_time__gte=now).order_by('start_time')
    upcoming_schedules = course.class_schedules.filter(start_time__gt=now).order_by('start_time')

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'live_schedules': live_schedules,
        'upcoming_schedules': upcoming_schedules,
    }
    return render(request, 'course_detail.html', context)

def live_classes_view(request):
    """
    Displays all live and upcoming classes across all courses.
    """
    now = timezone.now()

    live_classes = ClassSchedule.objects.select_related('course').filter(
        start_time__lte=now, end_time__gte=now
    ).order_by('start_time')

    upcoming_classes = ClassSchedule.objects.select_related('course').filter(
        start_time__gt=now
    ).order_by('start_time')

    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = list(Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True))

    context = {
        'live_classes': live_classes,
        'upcoming_classes': upcoming_classes,
        'user_enrollments': user_enrollments,
    }
    return render(request, 'live_classes.html', context)