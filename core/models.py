from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from students.models import Student


class StaffMember(models.Model):
    ROLE_CHOICES = [("TEACHER", "Teacher"), ("OTHER", "Other Staff"), ("DRIVER", "Driver")]
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="TEACHER")
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    joining_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff_profile")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"


class SalaryPayment(models.Model):
    staff = models.ForeignKey(StaffMember, on_delete=models.PROTECT, related_name="salary_payments")
    month = models.DateField(help_text="Use the first day of the salary month")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateField()
    method = models.CharField(max_length=20, choices=[("CASH","Cash"),("UPI","UPI"),("BANK","Bank Transfer"),("CHEQUE","Cheque")], default="BANK")
    reference = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]
        constraints = [models.UniqueConstraint(fields=["staff", "month"], name="one_salary_payment_per_staff_month")]

    def __str__(self):
        return f"{self.staff.full_name} - {self.month:%B %Y}"


class TransportRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="transport_records")
    route_name = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=30, blank=True)
    monthly_charge = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["student__full_name"]

    def __str__(self):
        return f"{self.student.full_name} - {self.route_name}"


class TransportPayment(models.Model):
    transport_record = models.ForeignKey(TransportRecord, on_delete=models.PROTECT, related_name="payments")
    month = models.DateField(help_text="Use the first day of the transport-fee month")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateField()
    method = models.CharField(max_length=20, choices=[("CASH","Cash"),("UPI","UPI"),("BANK","Bank Transfer"),("CHEQUE","Cheque")], default="CASH")
    reference = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"{self.transport_record.student.full_name} - {self.month:%B %Y} - Rs. {self.amount}"


class Exam(models.Model):
    name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=9, default="2026-2027")
    exam_date = models.DateField(null=True, blank=True)
    student_class = models.CharField(max_length=30)
    max_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("100.00"), validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-exam_date", "name"]

    def __str__(self):
        return f"{self.name} - Class {self.student_class}"


class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="exam_results")
    subject = models.CharField(max_length=100)
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["student__full_name", "subject"]
        constraints = [models.UniqueConstraint(fields=["exam", "student", "subject"], name="unique_exam_student_subject")]

    @property
    def percentage(self):
        if not self.exam.max_marks:
            return Decimal("0.00")
        return (self.marks_obtained / self.exam.max_marks) * Decimal("100")

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.exam_id and self.marks_obtained > self.exam.max_marks:
            raise ValidationError({"marks_obtained": "Marks obtained max marks se zyada nahi ho sakte."})

    def __str__(self):
        return f"{self.student.full_name} - {self.exam.name} - {self.subject}"


class TeacherAssignment(models.Model):
    """Class/section and module permissions explicitly granted by Principal."""
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name="assignments")
    student_class = models.CharField(max_length=30)
    section = models.CharField(max_length=10)
    can_attendance = models.BooleanField(default=True)
    can_exams = models.BooleanField(default=False)
    can_fees = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student_class", "section", "staff__full_name"]
        constraints = [models.UniqueConstraint(fields=["staff", "student_class", "section"], name="unique_teacher_class_section_assignment")]

    def __str__(self):
        return f"{self.staff.full_name} — Class {self.student_class}-{self.section}"
