
from datetime import date

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from students.models import Student
from .models import Attendance
from core.permissions import teacher_or_principal_required, teacher_permission_required, is_principal
from core.access import teacher_assignments, students_for_teacher


@require_http_methods(["GET", "POST"])
@teacher_permission_required("can_attendance")
def mark_attendance(request):
    today = timezone.localdate()

    selected_class = request.GET.get(
        "student_class",
        request.POST.get("student_class", ""),
    ).strip()

    selected_section = request.GET.get(
        "section",
        request.POST.get("section", ""),
    ).strip().upper()

    date_value = request.GET.get(
        "attendance_date",
        request.POST.get("attendance_date", today.isoformat()),
    ).strip()

    try:
        selected_date = date.fromisoformat(date_value)
    except (ValueError, TypeError):
        selected_date = today
        messages.error(request, "Please select a valid date.")

    active_students = Student.objects.filter(is_active=True)
    if not is_principal(request.user):
        active_students = students_for_teacher(request.user, "can_attendance")

    classes = (
        active_students
        .order_by("student_class")
        .values_list("student_class", flat=True)
        .distinct()
    )

    sections = []

    if selected_class:
        sections = (
            active_students
            .filter(student_class=selected_class)
            .order_by("section")
            .values_list("section", flat=True)
            .distinct()
        )

    students = Student.objects.none()
    attendance_records = {}

    if selected_class and selected_section:
        students = active_students.filter(
            student_class=selected_class,
            section=selected_section,
        ).order_by("full_name")

        attendance_records = {
            record.student_id: record
            for record in Attendance.objects.filter(
                student__in=students,
                attendance_date=selected_date,
            )
        }

    if request.method == "POST":
        if not selected_class or not selected_section:
            messages.error(
                request,
                "Please select a class and section first.",
            )
            return redirect("attendance:mark_attendance")

        student_ids = list(
            students.values_list("id", flat=True)
        )

        if not student_ids:
            messages.warning(
                request,
                "No active students found in this class and section.",
            )
            return redirect(
                f"{request.path}?student_class={selected_class}"
                f"&section={selected_section}"
                f"&attendance_date={selected_date.isoformat()}"
            )

        valid_statuses = {"PRESENT", "ABSENT", "LEAVE"}
        submitted_records = []

        for student_id in student_ids:
            status = request.POST.get(
                f"status_{student_id}", ""
            ).strip().upper()

            if status not in valid_statuses:
                messages.error(
                    request,
                    "Attendance was not saved. Select a valid status for every student.",
                )
                return redirect(
                    f"{request.path}?student_class={selected_class}"
                    f"&section={selected_section}"
                    f"&attendance_date={selected_date.isoformat()}"
                )

            remarks = request.POST.get(
                f"remarks_{student_id}", ""
            ).strip()[:255]

            submitted_records.append(
                (student_id, status, remarks)
            )

        try:
            with transaction.atomic():
                for student_id, status, remarks in submitted_records:
                    Attendance.objects.update_or_create(
                        student_id=student_id,
                        attendance_date=selected_date,
                        defaults={
                            "status": status,
                            "remarks": remarks,
                        },
                    )
        except Exception:
            messages.error(
                request,
                "Attendance could not be saved. Please check the error in your terminal.",
            )
        else:
            messages.success(
                request,
                f"Attendance saved successfully for {len(submitted_records)} students.",
            )

        return redirect(
            f"{request.path}?student_class={selected_class}"
            f"&section={selected_section}"
            f"&attendance_date={selected_date.isoformat()}"
        )

    student_rows = [
        {
            "student": student,
            "attendance": attendance_records.get(student.id),
        }
        for student in students
    ]

    present_count = sum(
        1 for row in student_rows
        if row["attendance"]
        and row["attendance"].status == "PRESENT"
    )

    absent_count = sum(
        1 for row in student_rows
        if row["attendance"]
        and row["attendance"].status == "ABSENT"
    )

    leave_count = sum(
        1 for row in student_rows
        if row["attendance"]
        and row["attendance"].status == "LEAVE"
    )

    context = {
        "classes": classes,
        "sections": sections,
        "student_rows": student_rows,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "selected_date": selected_date.isoformat(),
        "total_students": len(student_rows),
        "present_count": present_count,
        "absent_count": absent_count,
        "leave_count": leave_count,
    }

    return render(
        request,
        "attendance/mark_attendance.html",
        context,
    )
    
    
    
    
    
    
    
    
from calendar import monthrange
from datetime import date


@teacher_permission_required("can_attendance")
def attendance_reports(request):
    today = date.today()

    report_type = request.GET.get("report_type", "daily")
    if report_type not in ("daily", "monthly"):
        report_type = "daily"

    selected_class = request.GET.get("student_class", "").strip()
    selected_section = request.GET.get("section", "").strip().upper()

    try:
        selected_date = date.fromisoformat(
            request.GET.get("attendance_date", today.isoformat())
        )
    except (ValueError, TypeError):
        selected_date = today

    try:
        month_value = request.GET.get("month", today.strftime("%Y-%m"))
        month_start = date.fromisoformat(month_value + "-01")
    except (ValueError, TypeError):
        month_start = today.replace(day=1)

    last_day = monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=last_day)

    active_students = Student.objects.filter(is_active=True)
    if not is_principal(request.user):
        active_students = students_for_teacher(request.user, "can_attendance")

    classes = (
        active_students.order_by("student_class")
        .values_list("student_class", flat=True)
        .distinct()
    )

    sections = active_students.none().values_list("section", flat=True)

    if selected_class:
        sections = (
            active_students.filter(student_class=selected_class)
            .order_by("section")
            .values_list("section", flat=True)
            .distinct()
        )

    students = active_students

    if selected_class:
        students = students.filter(student_class=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

    if report_type == "daily":
        records = Attendance.objects.filter(
            student__in=students,
            attendance_date=selected_date,
        ).select_related("student").order_by("student__full_name")

        report_rows = [
            {
                "student": record.student,
                "status": record.get_status_display(),
                "remarks": record.remarks,
            }
            for record in records
        ]

        present_count = records.filter(status="PRESENT").count()
        absent_count = records.filter(status="ABSENT").count()
        leave_count = records.filter(status="LEAVE").count()

        marked_count = records.count()
        total_students = students.count()
        unmarked_count = max(total_students - marked_count, 0)

    else:
        records = Attendance.objects.filter(
            student__in=students,
            attendance_date__range=(month_start, month_end),
        ).values("student_id", "status")

        monthly_counts = {}

        for record in records:
            student_id = record["student_id"]

            if student_id not in monthly_counts:
                monthly_counts[student_id] = {
                    "present": 0,
                    "absent": 0,
                    "leave": 0,
                }

            if record["status"] == "PRESENT":
                monthly_counts[student_id]["present"] += 1
            elif record["status"] == "ABSENT":
                monthly_counts[student_id]["absent"] += 1
            elif record["status"] == "LEAVE":
                monthly_counts[student_id]["leave"] += 1

        report_rows = []

        for student in students.order_by("full_name"):
            counts = monthly_counts.get(
                student.id,
                {"present": 0, "absent": 0, "leave": 0},
            )

            present = counts["present"]
            absent = counts["absent"]
            leave = counts["leave"]
            total_marked = present + absent + leave

            percentage = (
                round(present * 100 / total_marked, 1)
                if total_marked
                else 0
            )

            report_rows.append({
                "student": student,
                "present": present,
                "absent": absent,
                "leave": leave,
                "total_marked": total_marked,
                "percentage": percentage,
            })

        present_count = sum(row["present"] for row in report_rows)
        absent_count = sum(row["absent"] for row in report_rows)
        leave_count = sum(row["leave"] for row in report_rows)
        total_students = len(report_rows)
        marked_count = sum(row["total_marked"] for row in report_rows)
        unmarked_count = sum(
            1 for row in report_rows if row["total_marked"] == 0
        )

    context = {
        "classes": classes,
        "sections": sections,
        "report_type": report_type,
        "selected_class": selected_class,
        "selected_section": selected_section,
        "selected_date": selected_date.isoformat(),
        "selected_month": month_start.strftime("%Y-%m"),
        "report_rows": report_rows,
        "present_count": present_count,
        "absent_count": absent_count,
        "leave_count": leave_count,
        "total_students": total_students,
        "marked_count": marked_count,
        "unmarked_count": unmarked_count,
    }

    return render(
        request,
        "attendance/attendance_reports.html",
        context,
    )






@teacher_permission_required("can_attendance")
def student_attendance_report(request):
    from datetime import date

    today = date.today()

    students = Student.objects.filter(is_active=True).order_by("full_name")
    if not is_principal(request.user):
        students = students_for_teacher(request.user, "can_attendance").order_by("full_name")

    selected_student_id = request.GET.get("student", "").strip()

    try:
        start_date = date.fromisoformat(
            request.GET.get(
                "start_date",
                today.replace(day=1).isoformat()
            )
        )
    except (ValueError, TypeError):
        start_date = today.replace(day=1)

    try:
        end_date = date.fromisoformat(
            request.GET.get("end_date", today.isoformat())
        )
    except (ValueError, TypeError):
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    selected_student = None
    records = Attendance.objects.none()

    present_count = 0
    absent_count = 0
    leave_count = 0
    total_marked = 0
    percentage = 0

    if selected_student_id.isdigit():
        selected_student = students.filter(
            pk=int(selected_student_id)
        ).first()

    if selected_student:
        records = Attendance.objects.filter(
            student=selected_student,
            attendance_date__range=(start_date, end_date),
        ).order_by("-attendance_date")

        present_count = records.filter(status="PRESENT").count()
        absent_count = records.filter(status="ABSENT").count()
        leave_count = records.filter(status="LEAVE").count()

        total_marked = (
            present_count + absent_count + leave_count
        )

        if total_marked:
            percentage = round(
                present_count * 100 / total_marked, 1
            )

    context = {
        "students": students,
        "selected_student": selected_student,
        "selected_student_id": selected_student_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "records": records,
        "present_count": present_count,
        "absent_count": absent_count,
        "leave_count": leave_count,
        "total_marked": total_marked,
        "percentage": percentage,
    }

    return render(
        request,
        "attendance/student_attendance_report.html",
        context,
    )