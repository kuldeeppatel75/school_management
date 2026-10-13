
from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("", views.fee_dashboard, name="dashboard"),
    path("plans/add/", views.fee_plan_create, name="plan_create"),
    path("payments/add/", views.payment_create, name="payment_create"),
    path("payments/history/", views.payment_history, name="payment_history"),
    path("payments/<int:pk>/receipt/", views.payment_receipt, name="receipt"),
]
