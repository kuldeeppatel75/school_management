from django.contrib import admin
from .models import TeacherAssignment, StaffMember, SalaryPayment, TransportRecord, TransportPayment, Exam, ExamResult


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "phone", "monthly_salary", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("full_name", "phone", "email")


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ("staff", "month", "amount", "payment_date", "method")
    list_filter = ("month", "method")
    search_fields = ("staff__full_name", "reference")


@admin.register(TransportRecord)
class TransportRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "route_name", "vehicle_number", "monthly_charge", "start_date")
    list_filter = ("route_name",)
    search_fields = ("student__full_name", "student__admission_number", "vehicle_number")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "student_class", "academic_year", "exam_date", "max_marks")
    list_filter = ("academic_year", "student_class")
    search_fields = ("name", "student_class")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "subject", "marks_obtained")
    list_filter = ("exam", "subject")
    search_fields = ("student__full_name", "student__admission_number", "subject")


@admin.register(TransportPayment)
class TransportPaymentAdmin(admin.ModelAdmin):
    list_display = ("transport_record", "month", "amount", "payment_date", "method")
    list_filter = ("month", "method")
    search_fields = ("transport_record__student__full_name", "reference")

admin.site.register(TeacherAssignment)
