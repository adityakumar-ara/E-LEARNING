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
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    feature_courses = Courses.objects.filter(
        is_featured=True,
        class_schedules__end_date__gte=today
    ).distinct().order_by('course_name')

    schedules_qs = ClassSchedule.objects.select_related('course').filter(
        end_date__gte=today
    ).order_by('start_date', 'start_time_of_day')

    live_schedules = []
    pending_schedules = []

    for schedule in schedules_qs:
        schedule_date = today if schedule.start_date <= today else schedule.start_date
        tz = timezone.get_current_timezone()
        schedule.start_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.start_time_of_day), tz)
        schedule.end_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.end_time_of_day), tz)

        if schedule.start_date <= today <= schedule.end_date:
            live_schedules.append(schedule)
        elif schedule.start_date > today:
            pending_schedules.append(schedule)

    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = list(Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True))

    context = {
        'videos': videos,
        'feature_courses': feature_courses,
        'live_schedules': live_schedules[:3],
        'pending_schedules': pending_schedules[:3],
        'user_enrollments': user_enrollments,
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
                request.session['otp_sent_at'] = timezone.now().isoformat()
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
    if 'registration_data' not in request.session:
        messages.error(request, 'Session expired or invalid request. Please register again.')
        return redirect('register')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['otp'] == str(request.session.get('otp')):
                user_data = request.session.pop('registration_data')
                request.session.pop('otp_sent_at', None)
                request.session.pop('otp')

                email = user_data['email']
                phone = user_data['phone']
                
                # First, check if email already exists
                existing_user = CustomeUser.objects.filter(email=email).first()
                
                if existing_user:
                    # User exists - just update their info and login
                    existing_user.full_name = user_data['full_name']
                    existing_user.phone = phone
                    existing_user.gender = user_data.get('gender', '')
                    existing_user.set_password(user_data['password'])
                    existing_user.save()
                    messages.success(request, 'Welcome! Your account has been updated successfully.')
                    login(request, existing_user)
                    return redirect('home')
                else:
                    # Brand new user - check if phone is already taken by someone else
                    phone_exists = CustomeUser.objects.filter(phone=phone).exists()
                    
                    if phone_exists:
                        messages.error(request, "This phone number is already registered. Please use a different phone number or login with your existing account.")
                        return redirect('register')
                    
                    # Create new user
                    try:
                        user = CustomeUser.objects.create_user(
                            username=email,
                            email=email,
                            password=user_data['password'],
                            full_name=user_data['full_name'],
                            phone=phone,
                            gender=user_data.get('gender', '')
                        )
                        messages.success(request, 'Welcome! Your account has been created successfully.')
                        login(request, user)
                        return redirect('home')
                    except Exception as e:
                        messages.error(request, f"Error creating account: {str(e)}")
                        return redirect('register')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'verify_otp.html', {'form': form})

def resend_otp(request):
    if 'registration_data' not in request.session:
        messages.error(request, 'Session expired. Please start the registration process again.')
        return redirect('register')

    # Simple rate-limiting: allow resend only after 60 seconds
    last_sent_time_str = request.session.get('otp_sent_at')
    if last_sent_time_str:
        last_sent_time = timezone.datetime.fromisoformat(last_sent_time_str)
        if timezone.now() - last_sent_time < timezone.timedelta(seconds=60):
            messages.warning(request, 'Please wait at least 60 seconds before requesting a new OTP.')
            return redirect('verify_otp')

    user_data = request.session['registration_data']
    otp = random.randint(100000, 999999)

    subject = 'Your New Email Verification OTP'
    message = f'Hello {user_data["full_name"]},\n\nYour new OTP for registration is: {otp}\n\nThank you!'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')
    to_email = [user_data['email']]

    try:
        send_mail(subject, message, from_email, to_email)
        # Update session with new OTP and timestamp
        request.session['otp'] = otp
        request.session['otp_sent_at'] = timezone.now().isoformat()
        messages.success(request, 'A new OTP has been sent to your email.')
    except Exception as e:
        messages.error(request, f'Failed to send OTP email. Error: {e}')

    return redirect('verify_otp')


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

    # Updated logic for recurring schedules
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    live_schedules = []
    upcoming_schedules = []

    # Find all schedules for this course that are active today or in the future
    active_schedules = course.class_schedules.filter(end_date__gte=today).order_by('start_date', 'start_time_of_day')

    tz = timezone.get_current_timezone()
    for schedule in active_schedules:
        # Create timezone-aware start and end datetimes for today
        start_dt = timezone.make_aware(timezone.datetime.combine(today, schedule.start_time_of_day), tz)
        end_dt = timezone.make_aware(timezone.datetime.combine(today, schedule.end_time_of_day), tz)

        schedule.start_time = start_dt
        schedule.end_time = end_dt

        if schedule.is_live:
            live_schedules.append(schedule)
        elif schedule.start_date > today or (schedule.start_date == today and schedule.start_time_of_day > current_time):
            upcoming_schedules.append(schedule)

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
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    # Find all schedules that are active today
    schedules_qs = ClassSchedule.objects.select_related('course').filter(
        end_date__gte=today
    ).order_by('start_date', 'start_time_of_day')

    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = list(Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True))
    enrolled_set = set(user_enrollments)

    all_schedules = []
    tz = timezone.get_current_timezone()
    for schedule in schedules_qs:
        schedule_date = today if schedule.start_date <= today else schedule.start_date
        schedule.start_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.start_time_of_day), tz)
        schedule.end_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.end_time_of_day), tz)

        schedule.is_enrolled = schedule.course.id in enrolled_set
        schedule.is_active_today = schedule.start_date <= today <= schedule.end_date

        if schedule.is_active_today:
            if current_time < schedule.start_time_of_day:
                schedule.current_status = 'wait'
            elif schedule.start_time_of_day <= current_time <= schedule.end_time_of_day:
                schedule.current_status = 'join' if schedule.is_enrolled and schedule.meeting_link else 'enroll' if not schedule.is_enrolled else 'wait'
            else:
                schedule.current_status = 'wait'
        else:
            schedule.current_status = 'wait'

        all_schedules.append(schedule)

    context = {
        'all_schedules': all_schedules,
        'user_enrollments': user_enrollments,
    }
    return render(request, 'live_classes.html', context)