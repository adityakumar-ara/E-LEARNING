from .models import Courses

def all_courses_for_nav(request):
    courses = Courses.objects.all().order_by('course_name')
    return {'all_courses_for_nav': courses}