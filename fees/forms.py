
from django import forms
from django.core.exceptions import ValidationError

from .models import FeePlan, FeePayment


class FeePlanForm(forms.ModelForm):
    class Meta:
        model = FeePlan
        fields = [
            "student",
            "academic_year",
            "total_fee",
            "discount",
            "due_date",
            "remarks",
        ]
        widgets = {
            "student": forms.Select(attrs={
                "class": "form-select",
            }),
            "academic_year": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "2026-2027",
            }),
            "total_fee": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "Total fees",
            }),
            "discount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "Discount (if any)",
            }),
            "due_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional notes",
            }),
        }

    def clean_academic_year(self):
        year = self.cleaned_data["academic_year"].strip()
        if len(year) != 9 or year[4] != "-":
            raise ValidationError(
                "Academic year 2026-2027 ke format mein likhein."
            )
        if not (year[:4].isdigit() and year[5:].isdigit()):
            raise ValidationError(
                "Academic year mein dono taraf 4-digit year likhein."
            )
        return year

    def clean(self):
        cleaned_data = super().clean()
        total_fee = cleaned_data.get("total_fee")
        discount = cleaned_data.get("discount")

        if (
            total_fee is not None
            and discount is not None
            and discount > total_fee
        ):
            self.add_error(
                "discount",
                "Discount total fee se zyada nahi ho sakta.",
            )

        return cleaned_data


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = [
            "fee_plan",
            "payment_date",
            "amount",
            "payment_method",
            "month_for",
            "receipt_number",
            "transaction_reference",
            "remarks",
        ]
        widgets = {
            "fee_plan": forms.Select(attrs={
                "class": "form-select",
            }),
            "payment_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0.01",
                "step": "0.01",
                "placeholder": "Payment amount",
            }),
            "payment_method": forms.Select(attrs={
                "class": "form-select",
            }),
            "month_for": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "April 2026 / Annual Fee",
            }),
            "receipt_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional receipt number",
            }),
            "transaction_reference": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional UPI/bank reference",
            }),
            "remarks": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional notes",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fee_plan"].queryset = (
            FeePlan.objects.select_related("student").order_by(
                "student__full_name",
                "academic_year",
            )
        )
    
    def clean_receipt_number(self):
        receipt_number = self.cleaned_data.get("receipt_number")
        return receipt_number or None
