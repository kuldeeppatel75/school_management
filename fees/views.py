
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import FeePlanForm, FeePaymentForm
from .models import FeePlan, FeePayment
from core.permissions import principal_required, teacher_permission_required, is_principal
from core.access import students_for_teacher


@teacher_permission_required("can_fees")
def fee_dashboard(request):
    plans_qs = FeePlan.objects.select_related("student").prefetch_related("payments")
    if not is_principal(request.user):
        allowed_students = students_for_teacher(request.user, "can_fees")
        plans_qs = plans_qs.filter(student__in=allowed_students)
    q = request.GET.get("q", "").strip()
    klass = request.GET.get("student_class", "").strip()
    section = request.GET.get("section", "").strip().upper()
    if q:
        from django.db.models import Q
        plans_qs = plans_qs.filter(Q(student__full_name__icontains=q) | Q(student__admission_number__icontains=q) | Q(student__phone__icontains=q))
    if klass:
        plans_qs = plans_qs.filter(student_class=klass)
    if section:
        plans_qs = plans_qs.filter(section=section)
    fee_plans = list(plans_qs.order_by("student_class", "section", "student__full_name"))

    total_fee = sum(
        (plan.payable_amount for plan in fee_plans),
        start=Decimal("0.00"),
    )

    total_paid = sum(
        (plan.total_paid for plan in fee_plans),
        start=Decimal("0.00"),
    )

    context = {
        "fee_plans": fee_plans,
        "total_plans": len(fee_plans),
        "total_fee": total_fee,
        "total_paid": total_paid,
        "total_balance": total_fee - total_paid,
        "total_payments": FeePayment.objects.filter(is_reversed=False, fee_plan__in=plans_qs).count(),
        "search_q": q, "selected_class": klass, "selected_section": section,
        "classes": plans_qs.values_list("student_class", flat=True).distinct(),
        "sections": plans_qs.values_list("section", flat=True).distinct(),
    }

    return render(request, "fees/dashboard.html", context)


@teacher_permission_required("can_fees")
def fee_plan_create(request):
    if request.method == "POST":
        form = FeePlanForm(request.POST)
        if not is_principal(request.user):
            form.fields["student"].queryset = students_for_teacher(request.user, "can_fees")

        if form.is_valid():
            plan = form.save()

            messages.success(
                request,
                f"{plan.student.full_name} ka Fee Plan successfully save ho gaya.",
            )

            return redirect("fees:dashboard")
    else:
        form = FeePlanForm()
        if not is_principal(request.user):
            form.fields["student"].queryset = students_for_teacher(request.user, "can_fees")

    return render(
        request,
        "fees/feeplan_form.html",
        {"form": form},
    )


@teacher_permission_required("can_fees")
def payment_create(request):
    if request.method == "POST":
        form = FeePaymentForm(request.POST)
        if not is_principal(request.user):
            form.fields["fee_plan"].queryset = FeePlan.objects.filter(student__in=students_for_teacher(request.user, "can_fees")).select_related("student")

        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)

                # Payment save karne se pehle fee plan ko lock karo.
                plan = (
                    FeePlan.objects
                    .select_for_update()
                    .get(pk=payment.fee_plan_id)
                )

                # Amount aur remaining balance dobara check karo.
                other_payments = FeePayment.objects.filter(
                    fee_plan=plan,
                    is_reversed=False,
                )

                paid_before = sum(
                    other_payments.values_list("amount", flat=True),
                    start=Decimal("0.00"),
                )

                remaining = plan.payable_amount - paid_before

                if payment.amount <= 0:
                    form.add_error(
                        "amount",
                        "Payment amount zero se zyada hona chahiye.",
                    )
                elif payment.amount > remaining:
                    form.add_error(
                        "amount",
                        f"Remaining balance sirf Rs. {remaining:.2f} hai.",
                    )
                else:
                    payment.save()

                    # Agar receipt number nahi diya, to automatic banao.
                    if not payment.receipt_number:
                        payment.receipt_number = (
                            f"SP-{payment.payment_date:%Y%m%d}-"
                            f"{payment.pk:06d}"
                        )
                        payment.save(update_fields=["receipt_number"])

                    messages.success(
                        request,
                        f"Payment successfully save ho gayi. "
                        f"Receipt: {payment.receipt_number}",
                    )

                    return redirect(
                        "fees:receipt",
                        pk=payment.pk,
                    )
    else:
        form = FeePaymentForm()
        if not is_principal(request.user):
            form.fields["fee_plan"].queryset = FeePlan.objects.filter(student__in=students_for_teacher(request.user, "can_fees")).select_related("student")
        form.fields["payment_date"].initial = timezone.localdate()

    return render(
        request,
        "fees/payment_form.html",
        {"form": form},
    )


@teacher_permission_required("can_fees")
def payment_history(request):
    payments = FeePayment.objects.select_related("fee_plan", "fee_plan__student").order_by("-payment_date", "-id")
    if not is_principal(request.user):
        payments = payments.filter(fee_plan__student__in=students_for_teacher(request.user, "can_fees"))
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        payments = payments.filter(Q(fee_plan__student__full_name__icontains=q) | Q(fee_plan__student__admission_number__icontains=q) | Q(receipt_number__icontains=q))

    return render(
        request,
        "fees/payment_history.html",
        {"payments": payments},
    )


@teacher_permission_required("can_fees")
def payment_receipt(request, pk):
    payment_qs = FeePayment.objects.select_related("fee_plan", "fee_plan__student")
    if not is_principal(request.user):
        payment_qs = payment_qs.filter(fee_plan__student__in=students_for_teacher(request.user, "can_fees"))
    payment = get_object_or_404(payment_qs, pk=pk)

    return render(
        request,
        "fees/receipt.html",
        {"payment": payment},
    )
