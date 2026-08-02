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
from django.urls import reverse
import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from .models import *

def home(request):
    videos = ELVideo.objects.all()
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    feature_courses = Courses.objects.filter(
        is_featured=True,
        class_schedules__start_date__gt=today,
    ).exclude(
        class_schedules__start_date__lte=today
    ).distinct().order_by('course_name')

    schedules_qs = ClassSchedule.objects.select_related('course').order_by(
        'start_date', 'start_time_of_day'
    )

    live_schedules = []
    pending_schedules = []

    for schedule in schedules_qs:
        schedule_date = today if schedule.start_date <= today else schedule.start_date
        tz = timezone.get_current_timezone()
        schedule.start_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.start_time_of_day), tz)
        schedule.end_time = timezone.make_aware(timezone.datetime.combine(schedule_date, schedule.end_time_of_day), tz)

        # Once a class has reached its start date, it stays in the homepage Live section.
        # Only not-yet-started classes are kept in Upcoming and Featured sections.
        if schedule.start_date <= today:
            live_schedules.append(schedule)
        else:
            pending_schedules.append(schedule)

    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = list(Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True))

    context = {
        'videos': videos,
        'feature_courses': feature_courses,
        'live_schedules': live_schedules,
        'pending_schedules': pending_schedules,
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


def create_razorpay_order(amount, receipt):
    """Create a Razorpay order using the server-side secret key."""
    payload = json.dumps({
        'amount': amount,
        'currency': 'INR',
        'receipt': receipt,
    }).encode('utf-8')
    credentials = f'{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}'
    authorization = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    request = urllib.request.Request(
        'https://api.razorpay.com/v1/orders',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Basic {authorization}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        details = error.read().decode('utf-8')
        raise ValueError(details or 'Razorpay could not create an order.')
    except urllib.error.URLError as error:
        raise ValueError('Unable to connect to Razorpay. Please try again.') from error


def enroll_course(request, course_id):
    """Create a Razorpay order for a paid course or enroll immediately if free."""
    if not request.user.is_authenticated:
        return redirect(f'{reverse("login")}?next={request.path}')
    if request.method != 'POST':
        return redirect('course_detail', course_id=course_id)

    course = get_object_or_404(Courses, id=course_id)
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', course_id=course.id)

    price = course.discount_price if course.discount_price is not None else course.price
    if not price or price <= 0:
        Enrollment.objects.get_or_create(user=request.user, course=course)
        messages.success(request, 'You have been enrolled successfully.')
        return redirect('course_detail', course_id=course.id)

    amount = int(price * 100)  # Razorpay accepts the amount in paise.
    receipt = f'course-{course.id}-user-{request.user.id}-{timezone.now():%Y%m%d%H%M%S}'
    try:
        order = create_razorpay_order(amount, receipt)
    except ValueError as error:
        messages.error(request, f'Payment could not be started: {error}')
        return redirect('course_detail', course_id=course.id)

    return render(request, 'razorpay_checkout.html', {
        'course': course,
        'order': order,
        'amount': amount,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'callback_url': reverse('confirm_enrollment', args=[course.id]),
    })


def confirm_enrollment(request, course_id):
    """Verify Razorpay's signature and then create the course enrollment."""
    if not request.user.is_authenticated or request.method != 'POST':
        return redirect('course_detail', course_id=course_id)

    course = get_object_or_404(Courses, id=course_id)
    payment_id = request.POST.get('razorpay_payment_id', '')
    order_id = request.POST.get('razorpay_order_id', '')
    signature = request.POST.get('razorpay_signature', '')
    if not all((payment_id, order_id, signature)):
        messages.error(request, 'Payment verification details are missing.')
        return redirect('course_detail', course_id=course.id)

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        f'{order_id}|{payment_id}'.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        messages.error(request, 'Payment verification failed. You were not enrolled.')
        return redirect('course_detail', course_id=course.id)

    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, 'Payment successful. You are now enrolled in this course.')
    return redirect('course_detail', course_id=course.id)

def live_classes_view(request):
    """
    Displays all live and upcoming classes across all courses.
    """
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    # Include every saved schedule so the page is a complete class archive.
    all_schedules = ClassSchedule.objects.select_related('course').order_by(
        'start_date', 'start_time_of_day'
    )

    today_classes = []
    upcoming_classes = []

    user_enrollments = []
    if request.user.is_authenticated:
        user_enrollments = list(Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True))

    tz = timezone.get_current_timezone()
    for schedule in all_schedules:
        if schedule.start_date > today:
            schedule.start_time = timezone.make_aware(
                timezone.datetime.combine(schedule.start_date, schedule.start_time_of_day), tz
            )
            schedule.end_time = timezone.make_aware(
                timezone.datetime.combine(schedule.start_date, schedule.end_time_of_day), tz
            )
            schedule.is_enrolled = schedule.course.id in user_enrollments
            upcoming_classes.append(schedule)
            continue

        # Recurring classes use today's time while active; finished classes retain their last scheduled date.
        display_date = today if schedule.end_date >= today else schedule.end_date
        start_dt = timezone.make_aware(timezone.datetime.combine(display_date, schedule.start_time_of_day), tz)
        end_dt = timezone.make_aware(timezone.datetime.combine(display_date, schedule.end_time_of_day), tz)

        schedule.start_time = start_dt
        schedule.end_time = end_dt

        if schedule.start_date <= today <= schedule.end_date and schedule.start_time_of_day <= current_time <= schedule.end_time_of_day:
            schedule.activity_status = 'live'
        elif schedule.end_date >= today and current_time < schedule.start_time_of_day:
            schedule.activity_status = 'upcoming'
        else:
            schedule.activity_status = 'ended'

        schedule.is_enrolled = schedule.course.id in user_enrollments
        today_classes.append(schedule)

    context = {
        'today_classes': today_classes,
        'upcoming_classes': upcoming_classes,
        'live_count': sum(item.activity_status == 'live' for item in today_classes),
        'upcoming_count': sum(item.activity_status == 'upcoming' for item in today_classes) + len(upcoming_classes),
        'user_enrollments': user_enrollments,
    }
    return render(request, 'live_classes.html', context)
