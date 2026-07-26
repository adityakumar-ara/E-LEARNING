from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
# Register your models here.
from .models import *
class CustomeUserAdmin(UserAdmin):
    model = CustomeUser
    list_display = ('username', 'email', 'full_name', 'gender', 'is_staff')

    # Add custom fields to the user change form in the admin
    fieldsets = UserAdmin.fieldsets + (
            ('Custom Profile', {'fields': ('full_name', 'phone', 'dob', 'gender', 'profile_image')}),
    )
    # Add custom fields to the user creation form in the admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile', {'fields': ('full_name', 'phone', 'dob', 'gender', 'profile_image')}),
    )

admin.site.register(CustomeUser, CustomeUserAdmin)

@admin.register(ELVideo)
class ELvideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'alt')