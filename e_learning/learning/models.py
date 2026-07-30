from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.
class CustomeUser(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_image/', null=True, blank=True)

    def __str__(self):
        return self.email
    
class ELVideo(models.Model):
    video = models.FileField(upload_to="ELvideo/",null=True, blank=True)    
    alt = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return self.alt
    
class Courses(models.Model):
    course_name = models.CharField(max_length=200)
    about_course = models.TextField()
    course_image = models.ImageField(upload_to='feature_course/', null=True, blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_taught')
    starting_time = models.DateTimeField(null=True, blank=True)
    duration = models.CharField(max_length=100, help_text="e.g., '3 Months', '30 Hours'")
    is_featured = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Enter price in USD. Leave blank for free courses.")
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Enter a discount price if applicable.")

    def __str__(self):
        return self.course_name
    
class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course') # A user can only enroll in a course once

    def __str__(self):
        return f'{self.user.email} enrolled in {self.course.course_name}'

class Review(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)]) # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user')

    def __str__(self):
        return f'Review for {self.course.course_name} by {self.user.email}'

class ClassSchedule(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, related_name='class_schedules')
    title = models.CharField(max_length=200, help_text="e.g., 'Week 1: Introduction'")
    description = models.TextField(blank=True, null=True, help_text="A brief description of what will be covered in the class.")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    meeting_link = models.URLField(blank=True, null=True, help_text="Link to the live class (e.g., Zoom, Google Meet)")

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} for {self.course.course_name}"

    @property
    def is_live(self):
        """Returns True if the class is currently live."""
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    @property
    def is_upcoming(self):
        """Returns True if the class is in the future."""
        from django.utils import timezone
        now = timezone.now()
        return self.start_time > now