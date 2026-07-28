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
    
class Feature_Courses(models.model):
    course_name = models.CharField(max_length=100, null=True, blank=True)   
    about_course = models.TextField()
    course_image = models.ImageField(upload_to='feartur_course/', null=True, blank=True)
    