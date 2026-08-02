from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('courses/', views.course_view, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('recorded-class/<int:recorded_class_id>/enroll/', views.enroll_recorded_class, name='enroll_recorded_class'),
    path('course/<int:course_id>/payment/confirm/', views.confirm_enrollment, name='confirm_enrollment'),
    path('live-classes/', views.live_classes_view, name='live_classes'),
]
