from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('courses/', views.course_view, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('live-classes/', views.live_classes_view, name='live_classes'),
]