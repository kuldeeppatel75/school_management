
from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.mark_attendance, name="mark_attendance"),
    path("reports/", views.attendance_reports, name="attendance_reports"),
    path(
    "student-report/",
    views.student_attendance_report,
    name="student_attendance_report",
),
    
]
