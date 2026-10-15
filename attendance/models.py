
from django.db import models


class Attendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LEAVE", "Leave"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    attendance_date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PRESENT",
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-attendance_date", "student__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "attendance_date"],
                name="unique_student_attendance_per_day",
            )
        ]

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.attendance_date} - {self.get_status_display()}"
        )
