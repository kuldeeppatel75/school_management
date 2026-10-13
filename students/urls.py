from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.student_list, name="student_list"),
    path("add/", views.student_add, name="student_add"),
    path("<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("<int:pk>/delete/", views.student_delete, name="student_delete"),
]
