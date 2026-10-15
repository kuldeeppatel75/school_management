
from django.contrib import admin
from .models import FeePlan, FeePayment


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    fields = (
        "payment_date",
        "amount",
        "payment_method",
        "month_for",
        "receipt_number",
        "transaction_reference",
        "remarks",
    )
    readonly_fields = ("receipt_number",)


@admin.register(FeePlan)
class FeePlanAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "student_class",
        "section",
        "academic_year",
        "total_fee",
        "discount",
        "show_payable",
        "show_paid",
        "show_balance",
    )
    list_filter = (
        "academic_year",
        "student_class",
        "section",
    )
    search_fields = (
        "student__full_name",
        "student__admission_number",
    )
    inlines = [FeePaymentInline]

    @admin.display(description="Payable")
    def show_payable(self, obj):
        return obj.payable_amount

    @admin.display(description="Total Paid")
    def show_paid(self, obj):
        return obj.total_paid

    @admin.display(description="Balance")
    def show_balance(self, obj):
        return obj.balance


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "fee_plan",
        "payment_date",
        "amount",
        "payment_method",
        "month_for",
        "is_reversed",
    )
    list_filter = (
        "payment_date",
        "payment_method",
        "is_reversed",
    )
    search_fields = (
        "receipt_number",
        "fee_plan__student__full_name",
        "fee_plan__student__admission_number",
        "transaction_reference",
    )
    date_hierarchy = "payment_date"
    list_per_page = 25
