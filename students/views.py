from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models.deletion import ProtectedError
from .models import Student
from core.permissions import teacher_or_principal_required, principal_required, is_principal
from core.access import students_for_teacher


@teacher_or_principal_required
def student_list(request):
    students = Student.objects.all()
    if not is_principal(request.user):
        students = students_for_teacher(request.user)

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "all")

    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query)
            | Q(admission_number__icontains=search_query)
            | Q(student_class__icontains=search_query)
            | Q(section__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    if status_filter == "active":
        students = students.filter(is_active=True)
    elif status_filter == "inactive":
        students = students.filter(is_active=False)

    context = {
        "students": students,
        "total_students": students.count(),
        "active_students": students.filter(is_active=True).count(),
        "inactive_students": students.filter(is_active=False).count(),
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(
        request,
        "core/students/student_list.html",
        context,
    )


@principal_required
def student_add(request):
    if request.method == "POST":
        admission_number = request.POST.get(
            "admission_number", ""
        ).strip()
        full_name = request.POST.get("full_name", "").strip()
        father_name = request.POST.get("father_name", "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        gender = request.POST.get("gender", "").strip()
        student_class = request.POST.get("student_class", "").strip()
        section = request.POST.get("section", "").strip().upper()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not all([
            admission_number,
            full_name,
            father_name,
            gender,
            student_class,
            section,
            phone,
            address,
        ]):
            messages.error(
                request,
                "Please fill in all required fields."
            )

        elif len(section) > 10:
            messages.error(
                request,
                "Section must not exceed 10 characters."
            )

        elif Student.objects.filter(
            admission_number=admission_number
        ).exists():
            messages.error(
                request,
                "This admission number already exists."
            )

        elif gender not in {"MALE", "FEMALE", "OTHER"}:
            messages.error(
                request,
                "Please select a valid gender."
            )

        else:
            student = Student(
                admission_number=admission_number,
                full_name=full_name,
                father_name=father_name,
                date_of_birth=date_of_birth,
                gender=gender,
                student_class=student_class,
                section=section,
                phone=phone,
                email=email,
                address=address,
                is_active=is_active,
            )
            student.save()

            messages.success(
                request,
                f"Student {student.full_name} added successfully."
            )
            return redirect("students:student_list")

    return render(request, "core/students/student_form.html")


@principal_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        admission_number = request.POST.get(
            "admission_number", ""
        ).strip()
        full_name = request.POST.get("full_name", "").strip()
        father_name = request.POST.get("father_name", "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        gender = request.POST.get("gender", "").strip()
        student_class = request.POST.get("student_class", "").strip()
        section = request.POST.get("section", "").strip().upper()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not all([
            admission_number,
            full_name,
            father_name,
            gender,
            student_class,
            section,
            phone,
            address,
        ]):
            messages.error(
                request,
                "Please fill in all required fields."
            )

        elif len(section) > 10:
            messages.error(
                request,
                "Section must not exceed 10 characters."
            )

        elif Student.objects.filter(
            admission_number=admission_number
        ).exclude(pk=student.pk).exists():
            messages.error(
                request,
                "This admission number already exists."
            )

        elif gender not in {"MALE", "FEMALE", "OTHER"}:
            messages.error(
                request,
                "Please select a valid gender."
            )

        else:
            student.admission_number = admission_number
            student.full_name = full_name
            student.father_name = father_name
            student.date_of_birth = date_of_birth
            student.gender = gender
            student.student_class = student_class
            student.section = section
            student.phone = phone
            student.email = email
            student.address = address
            student.is_active = is_active
            student.save()

            messages.success(
                request,
                f"Student {student.full_name} updated successfully."
            )
            return redirect("students:student_list")

    return render(
        request,
        "core/students/student_form.html",
        {
            "student": student,
            "is_edit": True,
        },
    )




@require_POST
@principal_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student_name = student.full_name

    try:
        student.delete()

    except ProtectedError:
        student.is_active = False
        student.save(update_fields=["is_active"])

        messages.warning(
            request,
            (
                f"{student_name} ke fee records linked hain. "
                "Student ko permanently delete nahi kiya gaya; "
                "use inactive kar diya gaya hai. "
                "Fee records safe hain."
            ),
        )
        return redirect("students:student_list")

    messages.success(
        request,
        f"Student {student_name} deleted successfully."
    )

    return redirect("students:student_list")

