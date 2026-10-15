
from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "full_name",
        "father_name",
        "student_class",
        "phone",
        "gender",
        "is_active",
    )

    search_fields = (
        "admission_number",
        "full_name",
        "father_name",
        "phone",
        "email",
    )

    list_filter = (
        "student_class",
        "gender",
        "is_active",
    )

    ordering = ("full_name",)
    list_per_page = 20
