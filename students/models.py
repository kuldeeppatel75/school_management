from django.db import models
from django.conf import settings


class Student(models.Model):
    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="student_profile",
    )

    admission_number = models.CharField(
        max_length=30,
        unique=True
    )
    full_name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150)

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    student_class = models.CharField(max_length=30)

    # Student ka section: A, B, C etc.
    section = models.CharField(
        max_length=10,
        default="A"
    )

    phone = models.CharField(max_length=15)

    email = models.EmailField(
        blank=True
    )

    address = models.TextField()

    admission_date = models.DateField(
        auto_now_add=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["student_class", "section", "full_name"]

    def __str__(self):
        return (
            f"{self.admission_number} - "
            f"{self.full_name} "
            f"(Class {self.student_class}, "
            f"Section {self.section})"
        )
