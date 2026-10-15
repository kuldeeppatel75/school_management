from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import Attendance
from students.models import Student
from fees.models import FeePlan, FeePayment
from core.models import Exam, ExamResult


class Command(BaseCommand):
    help = "Add clearly labelled practice attendance, exam results and fee payments without deleting or overwriting existing records."

    @transaction.atomic
    def handle(self, *args, **options):
        students = list(Student.objects.filter(is_active=True).order_by("student_class", "section", "full_name"))
        if not students:
            self.stdout.write(self.style.WARNING("No active students found; demo records were not created."))
            return

        today = timezone.localdate()
        # Add five recent weekdays only where the student/date pair is still empty.
        day = today
        weekday_dates = []
        while len(weekday_dates) < 5:
            if day.weekday() < 5:
                weekday_dates.append(day)
            day -= timedelta(days=1)
        attendance_created = 0
        for student_index, student in enumerate(students):
            for day_index, attendance_date in enumerate(weekday_dates):
                status = "ABSENT" if (student_index + day_index) % 7 == 0 else "PRESENT"
                _, created = Attendance.objects.get_or_create(
                    student=student,
                    attendance_date=attendance_date,
                    defaults={"status": status, "remarks": "Demo practice record — not an official attendance entry"},
                )
                attendance_created += int(created)

        exams_created = 0
        results_created = 0
        for klass in sorted({student.student_class for student in students}):
            exam, created = Exam.objects.get_or_create(
                name="Practice Unit Test (Demo)",
                academic_year="2026-2027",
                student_class=klass,
                defaults={"exam_date": today, "max_marks": Decimal("100.00")},
            )
            exams_created += int(created)
            for student in students:
                if student.student_class != klass:
                    continue
                for subject_index, subject in enumerate(("Mathematics", "English")):
                    marks = Decimal(55 + ((student.pk * 7 + subject_index * 13) % 41))
                    _, created = ExamResult.objects.get_or_create(
                        exam=exam, student=student, subject=subject,
                        defaults={"marks_obtained": marks, "remarks": "Demo practice marks — replace with official result"},
                    )
                    results_created += int(created)

        # Add one clearly labelled partial payment only to fee plans with no payment history.
        payments_created = 0
        for plan in FeePlan.objects.select_related("student").all():
            paid = plan.total_paid
            remaining = plan.payable_amount - paid
            if remaining <= 0 or plan.payments.exists():
                continue
            amount = min(Decimal("1000.00"), remaining)
            FeePayment.objects.create(
                fee_plan=plan,
                payment_date=today,
                amount=amount,
                payment_method="CASH",
                month_for="Demo test payment",
                receipt_number=f"DEMO-{plan.pk}-{today:%Y%m%d}",
                remarks="DEMO ONLY — not a real fee payment",
            )
            payments_created += 1

        self.stdout.write(self.style.SUCCESS(
            "Demo data added without deleting/overwriting existing records: "
            f"attendance={attendance_created}, exams={exams_created}, "
            f"results={results_created}, demo_payments={payments_created}."
        ))
        self.stdout.write(self.style.WARNING(
            "These are practice records. Run only in a test copy of the database; clearly remove/void demo records before real school use."
        ))
