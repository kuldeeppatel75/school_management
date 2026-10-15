from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django import forms
from .models import HomePageSettings, StudentHighlight

from students.models import Student
from attendance.models import Attendance
from fees.models import FeePlan, FeePayment
from .models import StaffMember, SalaryPayment, TransportRecord, TransportPayment, Exam, ExamResult, TeacherAssignment
from .permissions import principal_required, teacher_permission_required
from .access import student_for_user, teacher_assignments, students_for_teacher


def is_principal(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name="PRINCIPAL").exists())


def role_name(user):
    if user.is_superuser or user.groups.filter(name="PRINCIPAL").exists():
        return "PRINCIPAL"
    if user.groups.filter(name="TEACHER").exists():
        return "TEACHER"
    if user.groups.filter(name="STUDENT").exists():
        return "STUDENT"
    return "UNASSIGNED"


def home(request):
    homepage = HomePageSettings.objects.filter(pk=1).first()
    highlights = StudentHighlight.objects.filter(is_published=True)
    return render(request, "core/home.html", {
        "total_students": Student.objects.filter(is_active=True).count(),
        "school_name": "Ramnarayan Yadav School, Khirkia",
        "homepage": homepage,
        "student_highlights": highlights,
        "can_manage_homepage": is_principal(request.user),
    })


class HomePageSettingsForm(forms.ModelForm):
    class Meta:
        model = HomePageSettings
        fields = ["hero_title", "hero_subtitle", "hero_description", "hero_image"]
        widgets = {
            "hero_title": forms.TextInput(attrs={"class": "form-control", "maxlength": 180}),
            "hero_subtitle": forms.TextInput(attrs={"class": "form-control", "maxlength": 240}),
            "hero_description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "hero_image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }


class StudentHighlightForm(forms.ModelForm):
    class Meta:
        model = StudentHighlight
        fields = ["student_name", "caption", "photo", "display_order", "is_published"]
        widgets = {
            "student_name": forms.TextInput(attrs={"class": "form-control"}),
            "caption": forms.TextInput(attrs={"class": "form-control"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


@principal_required
def homepage_manage(request):
    homepage, _ = HomePageSettings.objects.get_or_create(pk=1)
    if request.method == "POST":
        action = request.POST.get("form_action", "save_hero")
        if action == "add_highlight":
            highlight_form = StudentHighlightForm(request.POST, request.FILES)
            form = HomePageSettingsForm(instance=homepage)
            if highlight_form.is_valid():
                highlight_form.save()
                messages.success(request, "Student highlight publish ho gaya.")
                return redirect("homepage_manage")
        elif action == "delete_highlight":
            get_object_or_404(StudentHighlight, pk=request.POST.get("highlight_id")).delete()
            messages.success(request, "Student highlight delete ho gaya.")
            return redirect("homepage_manage")
        elif action == "toggle_highlight":
            highlight = get_object_or_404(StudentHighlight, pk=request.POST.get("highlight_id"))
            highlight.is_published = not highlight.is_published
            highlight.save(update_fields=["is_published"])
            messages.success(request, "Student highlight visibility update ho gayi.")
            return redirect("homepage_manage")
        else:
            form = HomePageSettingsForm(request.POST, request.FILES, instance=homepage)
            highlight_form = StudentHighlightForm()
            if form.is_valid():
                form.save()
                messages.success(request, "Homepage hero section update ho gaya.")
                return redirect("homepage_manage")
    else:
        form = HomePageSettingsForm(instance=homepage)
        highlight_form = StudentHighlightForm()
    return render(request, "core/homepage_manage.html", {
        "form": form, "highlight_form": highlight_form,
        "highlights": StudentHighlight.objects.all(), "homepage": homepage,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("portal")
    error = ""
    if request.method == "POST":
        selected_role = request.POST.get("role", "STUDENT").strip().upper()
        login_id = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = None
        if selected_role == "STUDENT":
            matches = Student.objects.filter(phone=login_id, is_active=True)
            if matches.count() == 1:
                student = matches.first()
                candidate = student.user
                if candidate is None:
                    candidate = User.objects.filter(username=student.phone).first()
                if candidate is None:
                    # Compatibility with earlier projects that used admission number as username.
                    candidate = User.objects.filter(username=student.admission_number).first()
                if candidate:
                    user = authenticate(request, username=candidate.username, password=password)
                    if user and not user.groups.filter(name="STUDENT").exists():
                        user = None
                    if user and student.user_id is None:
                        student.user = user
                        student.save(update_fields=["user"])
            elif matches.count() > 1:
                error = "Is phone number par ek se zyada active students hain. Principal se unique phone/login mapping karwayein."
        elif selected_role == "TEACHER":
            candidate = User.objects.filter(username=login_id).first()
            if candidate is None:
                staff = StaffMember.objects.filter(phone=login_id, role="TEACHER", is_active=True, user__isnull=False).select_related("user").first()
                candidate = staff.user if staff else None
            if candidate:
                user = authenticate(request, username=candidate.username, password=password)
                if user and not user.groups.filter(name="TEACHER").exists():
                    user = None
        elif selected_role == "PRINCIPAL":
            user = authenticate(request, username=login_id, password=password)
            if user and not is_principal(user):
                user = None
        else:
            error = "Login role select karein."
        if user is not None:
            login(request, user)
            return redirect("portal")
        if not error:
            error = "Phone/username ya password sahi nahi hai, ya is role ka access assign nahi hai."
    return render(request, "core/login.html", {"error": error})

@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def portal(request):
    role = role_name(request.user)
    if role == "UNASSIGNED":
        return render(request, "core/portal.html", {"role": role, "error": "Principal se account role assign karwayein."})
    if role == "STUDENT":
        student = student_for_user(request.user)
        if not student or not student.is_active:
            return render(request, "core/portal.html", {"role": role, "error": "Is account ka active admission record nahi mila. Principal se phone/login mapping check karwayein."})
        fee_plans = list(FeePlan.objects.filter(student=student).prefetch_related("payments"))
        attendance_all = Attendance.objects.filter(student=student)
        attendance_records = attendance_all.order_by("-attendance_date")[:15]
        results = ExamResult.objects.filter(student=student).select_related("exam").order_by("-exam__exam_date", "exam__name")
        context = {
            "role": role, "student": student, "fee_plans": fee_plans,
            "attendance_records": attendance_records, "results": results[:15],
            "present_total": attendance_all.filter(status="PRESENT").count(),
            "absent_total": attendance_all.filter(status="ABSENT").count(),
            "leave_total": attendance_all.filter(status="LEAVE").count(),
            "total_payable": sum((p.payable_amount for p in fee_plans), Decimal("0.00")),
            "total_paid": sum((p.total_paid for p in fee_plans), Decimal("0.00")),
            "total_balance": sum((p.balance for p in fee_plans), Decimal("0.00")),
            "all_results": results,
        }
        return render(request, "core/portal.html", context)
    if role == "TEACHER":
        assigned_students = students_for_teacher(request.user, "can_attendance")
        context = {
            "role": role,
            "total_students": assigned_students.count(),
            "teacher_assignments": teacher_assignments(request.user),
            "can_attendance": teacher_assignments(request.user, "can_attendance").exists(),
            "can_exams": teacher_assignments(request.user, "can_exams").exists(),
            "can_fees": teacher_assignments(request.user, "can_fees").exists(),
        }
        return render(request, "core/portal.html", context)
    context = {
        "role": role,
        "total_students": Student.objects.filter(is_active=True).count(),
        "total_staff": StaffMember.objects.filter(is_active=True).count(),
        "total_fee_plans": FeePlan.objects.count(),
        "collected_fees": FeePayment.objects.filter(is_reversed=False).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "total_exams": Exam.objects.count(),
        "recent_students": Student.objects.filter(is_active=True)[:8],
    }
    return render(request, "core/portal.html", context)


@principal_required
def account_create(request):
    students = Student.objects.filter(is_active=True, user__isnull=True).order_by("student_class", "section", "full_name")
    error = ""
    if request.method == "POST":
        role = request.POST.get("role", "").strip().upper()
        student_admission = request.POST.get("student_admission", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        username = (Student.objects.filter(admission_number=student_admission).values_list("phone", flat=True).first() or "") if role == "STUDENT" else phone
        password = request.POST.get("password", "")
        salary_raw = request.POST.get("monthly_salary", "0").strip() or "0"
        if role not in {"TEACHER", "STUDENT"} or not username or len(password) < 8:
            error = "Role, phone number aur kam se kam 8-character password sahi bharein."
        elif User.objects.filter(username=username).exists():
            error = "Ye phone number kisi login ka username ban chuka hai. Unique phone number use karein."
        elif role == "STUDENT" and not Student.objects.filter(admission_number=student_admission, is_active=True, user__isnull=True).exists():
            error = "Student select karein; uska account pehle se linked ho sakta hai."
        elif role == "STUDENT" and Student.objects.filter(phone=username, is_active=True).count() != 1:
            error = "Student ka phone number unique hona chahiye. Pehle admission record mein phone correct karein."
        elif role == "TEACHER" and not full_name:
            error = "Teacher ka full name zaroori hai."
        elif role == "TEACHER" and len(phone) > 15:
            error = "Teacher phone number 15 characters se chhota hona chahiye."
        else:
            try:
                salary = Decimal(salary_raw) if role == "TEACHER" else Decimal("0")
                if salary < 0:
                    raise ValueError
            except (ValueError, ArithmeticError):
                error = "Monthly salary zero ya positive amount honi chahiye."
            if not error:
                user = User.objects.create_user(username=username, password=password)
                group, _ = Group.objects.get_or_create(name=role)
                user.groups.add(group)
                if role == "STUDENT":
                    student = Student.objects.get(admission_number=student_admission)
                    student.user = user
                    student.email = request.POST.get("student_email", "").strip() or student.email
                    student.save(update_fields=["user", "email"])
                    user.first_name = student.full_name[:150]
                    user.email = student.email
                    user.save(update_fields=["first_name", "email"])
                else:
                    staff = StaffMember.objects.create(
                        full_name=full_name, role="TEACHER", phone=phone,
                        email=request.POST.get("email", "").strip(),
                        monthly_salary=salary, user=user,
                    )
                    klass = request.POST.get("student_class", "").strip()
                    section = request.POST.get("section", "").strip().upper()
                    if klass and section:
                        TeacherAssignment.objects.get_or_create(
                            staff=staff, student_class=klass, section=section,
                            defaults={
                                "can_attendance": request.POST.get("can_attendance") == "on",
                                "can_exams": request.POST.get("can_exams") == "on",
                                "can_fees": request.POST.get("can_fees") == "on",
                            },
                        )
                messages.success(request, f"{role.title()} login {username} create aur student/staff profile se link ho gaya.")
                return redirect("account_create")
    classes = Student.objects.filter(is_active=True).values_list("student_class", flat=True).distinct().order_by("student_class")
    return render(request, "core/account_create.html", {"students": students, "error": error, "classes": classes})


@principal_required
def teacher_access(request):
    teachers = StaffMember.objects.filter(role="TEACHER", is_active=True, user__isnull=False).order_by("full_name")
    classes = Student.objects.filter(is_active=True).values_list("student_class", flat=True).distinct().order_by("student_class")
    assignments = TeacherAssignment.objects.select_related("staff", "staff__user")
    error = ""
    if request.method == "POST":
        action = request.POST.get("action", "save")
        if action == "delete":
            assignment = get_object_or_404(TeacherAssignment, pk=request.POST.get("assignment_id"))
            assignment.delete()
            messages.success(request, "Teacher class/section access remove kar diya gaya.")
            return redirect("teacher_access")
        try:
            staff = teachers.get(pk=request.POST.get("staff"))
            klass = request.POST.get("student_class", "").strip()
            section = request.POST.get("section", "").strip().upper()
            if not Student.objects.filter(is_active=True, student_class=klass, section=section).exists():
                raise ValueError("Selected class-section mein active students nahi hain.")
            TeacherAssignment.objects.update_or_create(
                staff=staff, student_class=klass, section=section,
                defaults={
                    "can_attendance": request.POST.get("can_attendance") == "on",
                    "can_exams": request.POST.get("can_exams") == "on",
                    "can_fees": request.POST.get("can_fees") == "on",
                },
            )
            messages.success(request, f"{staff.full_name} ko Class {klass}-{section} ka selected access assign ho gaya.")
            return redirect("teacher_access")
        except (StaffMember.DoesNotExist, ValueError) as exc:
            error = str(exc) or "Teacher aur class/section select karein."
    return render(request, "core/teacher_access.html", {"teachers": teachers, "classes": classes, "assignments": assignments, "error": error})

@principal_required
def staff_list(request):
    staff = StaffMember.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        staff = staff.filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(role__icontains=q))
    return render(request, "core/staff_list.html", {"staff": staff, "q": q})


@principal_required
def staff_create(request):
    error = ""
    data = {
        "full_name": "",
        "role": "TEACHER",
        "phone": "",
        "email": "",
        "address": "",
        "monthly_salary": "0.00",
        "joining_date": date.today().isoformat(),
        "is_active": True,
    }

    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "role": request.POST.get("role", "TEACHER").strip().upper(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "monthly_salary": request.POST.get("monthly_salary", "0").strip(),
            "joining_date": request.POST.get("joining_date", "").strip(),
            "is_active": request.POST.get("is_active") == "on",
        }
        try:
            salary = Decimal(data["monthly_salary"] or "0")
            joining_date = date.fromisoformat(data["joining_date"]) if data["joining_date"] else None
            valid_roles = {choice[0] for choice in StaffMember.ROLE_CHOICES}
            if not data["full_name"]:
                raise ValueError("Staff member ka naam zaroori hai.")
            if data["role"] not in valid_roles:
                raise ValueError("Please valid staff role select karein.")
            if salary < 0:
                raise ValueError("Monthly salary negative nahi ho sakti.")
            if len(data["phone"]) > 15:
                raise ValueError("Phone number 15 characters se chhota hona chahiye.")
            if data["email"]:
                from django.core.validators import validate_email
                validate_email(data["email"])
        except Exception as exc:
            error = str(exc) if isinstance(exc, ValueError) and str(exc) else "Form details check karein. Salary, email aur joining date sahi bharein."
        else:
            StaffMember.objects.create(
                full_name=data["full_name"],
                role=data["role"],
                phone=data["phone"],
                email=data["email"],
                address=data["address"],
                monthly_salary=salary,
                joining_date=joining_date,
                is_active=data["is_active"],
            )
            messages.success(request, f"{data['full_name']} ka staff record save ho gaya.")
            return redirect("staff_list")

    return render(request, "core/staff_form.html", {
        "data": data, "error": error, "is_edit": False,
    })


@principal_required
def staff_edit(request, pk):
    person = get_object_or_404(StaffMember, pk=pk)
    error = ""
    data = {
        "full_name": person.full_name,
        "role": person.role,
        "phone": person.phone,
        "email": person.email,
        "address": person.address,
        "monthly_salary": str(person.monthly_salary),
        "joining_date": person.joining_date.isoformat() if person.joining_date else "",
        "is_active": person.is_active,
    }

    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "role": request.POST.get("role", "TEACHER").strip().upper(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "monthly_salary": request.POST.get("monthly_salary", "0").strip(),
            "joining_date": request.POST.get("joining_date", "").strip(),
            "is_active": request.POST.get("is_active") == "on",
        }
        try:
            salary = Decimal(data["monthly_salary"] or "0")
            joining_date = date.fromisoformat(data["joining_date"]) if data["joining_date"] else None
            valid_roles = {choice[0] for choice in StaffMember.ROLE_CHOICES}
            if not data["full_name"]:
                raise ValueError("Staff member ka naam zaroori hai.")
            if data["role"] not in valid_roles:
                raise ValueError("Please valid staff role select karein.")
            if salary < 0:
                raise ValueError("Monthly salary negative nahi ho sakti.")
            if len(data["phone"]) > 15:
                raise ValueError("Phone number 15 characters se chhota hona chahiye.")
            if data["email"]:
                from django.core.validators import validate_email
                validate_email(data["email"])
        except Exception as exc:
            error = str(exc) if isinstance(exc, ValueError) and str(exc) else "Form details check karein. Salary, email aur joining date sahi bharein."
        else:
            person.full_name = data["full_name"]
            person.role = data["role"]
            person.phone = data["phone"]
            person.email = data["email"]
            person.address = data["address"]
            person.monthly_salary = salary
            person.joining_date = joining_date
            person.is_active = data["is_active"]
            person.save()
            messages.success(request, f"{person.full_name} ka staff record update ho gaya.")
            return redirect("staff_list")

    return render(request, "core/staff_form.html", {
        "data": data, "error": error, "is_edit": True, "person": person,
    })


@principal_required
def salary_dashboard(request):
    staff = StaffMember.objects.filter(is_active=True)
    month_str = request.GET.get("month", date.today().strftime("%Y-%m"))
    try:
        month = date.fromisoformat(month_str + "-01")
    except ValueError:
        month = date.today().replace(day=1)
        month_str = month.strftime("%Y-%m")
    payments = SalaryPayment.objects.filter(month=month).values("staff_id").annotate(total=Sum("amount"))
    paid_by_staff = {p["staff_id"]: p["total"] for p in payments}
    rows = []
    total_due = Decimal("0.00")
    total_paid = Decimal("0.00")
    for person in staff:
        paid = paid_by_staff.get(person.id, Decimal("0.00"))
        due = max(person.monthly_salary - paid, Decimal("0.00"))
        rows.append({"staff": person, "paid": paid, "due": due})
        total_paid += paid
        total_due += due
    return render(request, "core/salary_dashboard.html", {"rows": rows, "month": month_str, "total_paid": total_paid, "total_due": total_due})


@principal_required
def salary_payment_create(request):
    staff = StaffMember.objects.filter(is_active=True)
    error = ""
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        month_str = request.POST.get("month")
        amount_raw = request.POST.get("amount", "0")
        payment_date = request.POST.get("payment_date") or date.today().isoformat()
        try:
            person = staff.get(pk=staff_id)
            month = date.fromisoformat(month_str + "-01")
            amount = Decimal(amount_raw)
            paid = SalaryPayment.objects.filter(staff=person, month=month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if amount <= 0 or amount > person.monthly_salary - paid:
                error = f"Amount 0 se zyada aur remaining salary se kam/barabar hona chahiye. Remaining: ₹{person.monthly_salary-paid:.2f}"
            elif SalaryPayment.objects.filter(staff=person, month=month).exists():
                error = "Is staff member aur month ki salary entry pehle se hai. Existing entry edit karne ke liye admin panel use karein."
            else:
                SalaryPayment.objects.create(staff=person, month=month, amount=amount, payment_date=date.fromisoformat(payment_date), method=request.POST.get("method", "BANK"), reference=request.POST.get("reference", "").strip(), remarks=request.POST.get("remarks", "").strip())
                messages.success(request, "Salary payment save ho gayi.")
                return redirect("salary_dashboard")
        except (StaffMember.DoesNotExist, ValueError, ArithmeticError):
            error = "Please form ke saare required fields sahi bharein."
    return render(request, "core/salary_payment_form.html", {"staff": staff, "error": error, "today": date.today().isoformat(), "month": date.today().strftime("%Y-%m")})


@principal_required
def transport_list(request):
    records = TransportRecord.objects.select_related("student")
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        records = records.filter(Q(student__full_name__icontains=q) | Q(student__admission_number__icontains=q) | Q(route_name__icontains=q))
    month_str = request.GET.get("month", date.today().strftime("%Y-%m"))
    try:
        month = date.fromisoformat(month_str + "-01")
    except ValueError:
        month = date.today().replace(day=1)
        month_str = month.strftime("%Y-%m")
    rows = []
    for record in records:
        paid = record.payments.filter(month=month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        rows.append({"record": record, "paid": paid, "balance": max(record.monthly_charge - paid, Decimal("0.00"))})
    return render(request, "core/transport_list.html", {"records": rows, "q": q, "month": month_str})


@principal_required
def transport_payment_create(request):
    records = TransportRecord.objects.select_related("student").all()
    error = ""
    if request.method == "POST":
        try:
            record = records.get(pk=request.POST.get("transport_record"))
            month = date.fromisoformat(request.POST.get("month", "") + "-01")
            amount = Decimal(request.POST.get("amount", "0"))
            paid = record.payments.filter(month=month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if amount <= 0 or amount > record.monthly_charge - paid:
                error = f"Amount positive aur remaining charge se kam/barabar hona chahiye. Remaining: ₹{record.monthly_charge-paid:.2f}"
            else:
                TransportPayment.objects.create(
                    transport_record=record, month=month, amount=amount,
                    payment_date=date.fromisoformat(request.POST.get("payment_date", "")),
                    method=request.POST.get("method", "CASH"),
                    reference=request.POST.get("reference", "").strip(),
                    remarks=request.POST.get("remarks", "").strip(),
                )
                messages.success(request, "Transport payment save ho gayi.")
                return redirect("transport_list")
        except (TransportRecord.DoesNotExist, ValueError, ArithmeticError):
            error = "Transport record, month, amount aur payment date sahi bharein."
    return render(request, "core/transport_payment_form.html", {
        "records": records, "error": error, "month": date.today().strftime("%Y-%m"),
        "today": date.today().isoformat(),
    })


@principal_required
def transport_create(request):
    students = Student.objects.filter(is_active=True)
    error = ""
    if request.method == "POST":
        try:
            student = students.get(pk=request.POST.get("student"))
            route = request.POST.get("route_name", "").strip()
            charge = Decimal(request.POST.get("monthly_charge", "0"))
            start = date.fromisoformat(request.POST.get("start_date", ""))
            if not route or charge < 0:
                raise ValueError
            TransportRecord.objects.create(student=student, route_name=route, vehicle_number=request.POST.get("vehicle_number", "").strip(), monthly_charge=charge, start_date=start, notes=request.POST.get("notes", "").strip())
            messages.success(request, "Transport record save ho gaya.")
            return redirect("transport_list")
        except (Student.DoesNotExist, ValueError, ArithmeticError):
            error = "Student, route, charge aur start date sahi bharein."
    return render(request, "core/transport_form.html", {"students": students, "error": error, "today": date.today().isoformat()})


@teacher_permission_required("can_exams")
def exam_list(request):
    exams = Exam.objects.all()
    if not is_principal(request.user):
        allowed_classes = teacher_assignments(request.user, "can_exams").values_list("student_class", flat=True)
        exams = exams.filter(student_class__in=allowed_classes)
    return render(request, "core/exam_list.html", {"exams": exams})


@teacher_permission_required("can_exams")
def exam_create(request):
    error = ""
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            year = request.POST.get("academic_year", "").strip()
            klass = request.POST.get("student_class", "").strip()
            max_marks = Decimal(request.POST.get("max_marks", "100"))
            exam_date = date.fromisoformat(request.POST["exam_date"]) if request.POST.get("exam_date") else None
            if not name or not klass or len(year) != 9 or year[4] != "-" or max_marks <= 0:
                raise ValueError
            if not is_principal(request.user) and not teacher_assignments(request.user, "can_exams").filter(student_class=klass).exists():
                raise ValueError("Principal ne is class ke exams ka access assign nahi kiya hai.")
            Exam.objects.create(name=name, academic_year=year, student_class=klass, max_marks=max_marks, exam_date=exam_date)
            messages.success(request, "Exam create ho gaya.")
            return redirect("exam_list")
        except (ValueError, ArithmeticError):
            error = "Exam details sahi bharein. Academic year 2026-2027 format mein hona chahiye."
    return render(request, "core/exam_form.html", {"error": error})


@teacher_permission_required("can_exams")
def result_create(request):
    exams = Exam.objects.all()
    students = Student.objects.filter(is_active=True)
    if not is_principal(request.user):
        assignments = teacher_assignments(request.user, "can_exams")
        exams = exams.filter(student_class__in=assignments.values_list("student_class", flat=True))
        students = students_for_teacher(request.user, "can_exams")
    error = ""
    if request.method == "POST":
        try:
            exam = exams.get(pk=request.POST.get("exam"))
            student = students.get(pk=request.POST.get("student"))
            subject = request.POST.get("subject", "").strip()
            marks = Decimal(request.POST.get("marks_obtained", "0"))
            if student.student_class != exam.student_class or not subject or marks < 0 or marks > exam.max_marks:
                raise ValueError
            if not is_principal(request.user) and not teacher_assignments(request.user, "can_exams").filter(student_class=student.student_class, section=student.section).exists():
                raise ValueError("Principal ne is student ke section ka exam access assign nahi kiya hai.")
            ExamResult.objects.update_or_create(exam=exam, student=student, subject=subject, defaults={"marks_obtained": marks, "remarks": request.POST.get("remarks", "").strip()})
            messages.success(request, "Student result save ho gaya.")
            return redirect("exam_list")
        except (Exam.DoesNotExist, Student.DoesNotExist, ValueError, ArithmeticError):
            error = "Exam, matching class ka student, subject aur marks sahi select karein."
    return render(request, "core/result_form.html", {"exams": exams, "students": students, "error": error})


def student_results(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if role_name(request.user) != "STUDENT":
        return redirect("portal")
    student = student_for_user(request.user)
    if not student or not student.is_active:
        return render(request, "core/portal.html", {"role": role_name(request.user), "error": "Student mapping nahi mili."})
    results = ExamResult.objects.filter(student=student).select_related("exam")
    return render(request, "core/student_results.html", {"student": student, "results": results})
