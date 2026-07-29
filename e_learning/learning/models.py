from django.db import models
from django.contrib.auth.models import AbstractUser
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
    starting_time = models.DateTimeField(null=True, blank=True)
    duration = models.CharField(max_length=100, help_text="e.g., '3 Months', '30 Hours'")
    is_featured = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Enter price in USD. Leave blank for free courses.")

    def __str__(self):
        return self.course_name
    