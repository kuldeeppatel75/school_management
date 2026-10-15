
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class FeePlan(models.Model):
    """
    Ek student ki ek academic year ki fee details.
    Ek hi student ke liye har academic year mein ek plan.
    """

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="fee_plans",
    )

    academic_year = models.CharField(
        max_length=9,
        help_text="Example: 2026-2027",
    )

    student_class = models.CharField(max_length=30)
    section = models.CharField(max_length=10)

    total_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    due_date = models.DateField(null=True, blank=True)

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "student_class",
            "section",
            "student__full_name",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_student_fee_plan_per_year",
            )
        ]

    def save(self, *args, **kwargs):
        # Class aur section ka snapshot rakho, taaki
        # baad mein student ki class badalne par
        # purane academic year ka record na badle.
        if self.student_id:
            self.student_class = self.student.student_class
            self.section = self.student.section

        super().save(*args, **kwargs)

    @property
    def payable_amount(self):
        return self.total_fee - self.discount

    @property
    def total_paid(self):
        result = self.payments.filter(
            is_reversed=False
        ).aggregate(total=Sum("amount"))

        return result["total"] or Decimal("0.00")

    @property
    def balance(self):
        return self.payable_amount - self.total_paid

    def clean(self):
        super().clean()

        if self.discount > self.total_fee:
            raise ValidationError({
                "discount": "Discount total fee se zyada nahi ho sakta."
            })

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.academic_year}"
        )


class FeePayment(models.Model):
    """
    Har jama payment ki alag entry.
    Purani payment ko overwrite karne ke bajaye
    reversal ka record use kiya ja sakta hai.
    """

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("BANK", "Bank Transfer"),
        ("CHEQUE", "Cheque"),
        ("CARD", "Card"),
        ("OTHER", "Other"),
    ]

    fee_plan = models.ForeignKey(
        FeePlan,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default="CASH",
    )

    month_for = models.CharField(
        max_length=30,
        blank=True,
        help_text="Example: April 2026 ya Annual Fee",
    )

    receipt_number = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
    )

    is_reversed = models.BooleanField(default=False)

    reversal_reason = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def clean(self):
        super().clean()

        if self.amount is None or self.amount <= 0:
            raise ValidationError({
                "amount": "Payment amount zero se zyada hona chahiye."
            })

        if self.fee_plan_id and not self.is_reversed:
            other_payments = self.fee_plan.payments.filter(
                is_reversed=False
            )

            if self.pk:
                other_payments = other_payments.exclude(pk=self.pk)

            paid_before = (
                other_payments.aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            remaining = self.fee_plan.payable_amount - paid_before

            if self.amount > remaining:
                raise ValidationError({
                    "amount": (
                        f"Payment balance se zyada hai. "
                        f"Maximum remaining amount: {remaining}"
                    )
                })

        if self.is_reversed and not self.reversal_reason.strip():
            raise ValidationError({
                "reversal_reason": (
                    "Payment reverse karne ka reason likhna zaroori hai."
                )
            })

    def __str__(self):
        return (
            f"{self.receipt_number or 'Receipt pending'} - "
            f"{self.fee_plan.student.full_name} - "
            f"Rs. {self.amount}"
        )
