from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("students", "0002_alter_student_options_student_section"),
    ]
    operations = [
        migrations.CreateModel(
            name="StaffMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=150)),
                ("role", models.CharField(choices=[("TEACHER", "Teacher"), ("OTHER", "Other Staff"), ("DRIVER", "Driver")], default="TEACHER", max_length=20)),
                ("phone", models.CharField(blank=True, max_length=15)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("monthly_salary", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("joining_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="staff_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.CreateModel(
            name="Exam",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("academic_year", models.CharField(default="2026-2027", max_length=9)),
                ("exam_date", models.DateField(blank=True, null=True)),
                ("student_class", models.CharField(max_length=30)),
                ("max_marks", models.DecimalField(decimal_places=2, default=Decimal("100.00"), max_digits=7, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-exam_date", "name"]},
        ),
        migrations.CreateModel(
            name="TransportRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("route_name", models.CharField(max_length=100)),
                ("vehicle_number", models.CharField(blank=True, max_length=30)),
                ("monthly_charge", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transport_records", to="students.student")),
            ],
            options={"ordering": ["student__full_name"]},
        ),
        migrations.CreateModel(
            name="TransportPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.DateField(help_text="Use the first day of the transport-fee month")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("payment_date", models.DateField()),
                ("method", models.CharField(choices=[("CASH", "Cash"), ("UPI", "UPI"), ("BANK", "Bank Transfer"), ("CHEQUE", "Cheque")], default="CASH", max_length=20)),
                ("reference", models.CharField(blank=True, max_length=100)),
                ("remarks", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("transport_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="core.transportrecord")),
            ],
            options={"ordering": ["-payment_date", "-id"]},
        ),
        migrations.CreateModel(
            name="SalaryPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.DateField(help_text="Use the first day of the salary month")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("payment_date", models.DateField()),
                ("method", models.CharField(choices=[("CASH", "Cash"), ("UPI", "UPI"), ("BANK", "Bank Transfer"), ("CHEQUE", "Cheque")], default="BANK", max_length=20)),
                ("reference", models.CharField(blank=True, max_length=100)),
                ("remarks", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("staff", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="salary_payments", to="core.staffmember")),
            ],
            options={"ordering": ["-payment_date", "-id"]},
        ),
        migrations.CreateModel(
            name="ExamResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=100)),
                ("marks_obtained", models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("remarks", models.CharField(blank=True, max_length=255)),
                ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="core.exam")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="exam_results", to="students.student")),
            ],
            options={"ordering": ["student__full_name", "subject"], "constraints": [models.UniqueConstraint(fields=("exam", "student", "subject"), name="unique_exam_student_subject")]},
        ),
    ]
