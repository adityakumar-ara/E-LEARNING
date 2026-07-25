from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.
class CustomeUser(AbstractUser):
    CHOOSE_GENDER=(
        ('male',('MALE')),
        ('female',('FEMALE')),
        ('other',('other')),
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, unique=True)
    dob = models.DateTimeField(max_length=10 , null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_image/', null=True, blank=True)
    def __str__(self):
        return self.email