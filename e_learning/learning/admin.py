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
    
class ClassScheduleInline(admin.TabularInline):
    model = ClassSchedule
    extra = 1 # Number of empty forms to display

@admin.register(Courses)    
class CoursesAdmin(admin.ModelAdmin)  :
    list_display = ('course_name', 'instructor', 'price', 'discount_price', 'is_featured', 'duration')
    list_filter = ('is_featured', 'starting_time')
    search_fields = ('course_name', 'about_course')
    raw_id_fields = ('instructor',)
    inlines = [ClassScheduleInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    search_fields = ('user__email', 'course__course_name')

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_time', 'end_time')
    list_filter = ('course', 'start_time')
    search_fields = ('title', 'course__course_name')