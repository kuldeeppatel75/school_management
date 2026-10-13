from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("portal/", views.portal, name="portal"),
    path("principal/accounts/add/", views.account_create, name="account_create"),
    path("principal/teacher-access/", views.teacher_access, name="teacher_access"),
    path("principal/staff/", views.staff_list, name="staff_list"),
    path("principal/staff/add/", views.staff_create, name="staff_create"),
    path("principal/staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("principal/salaries/", views.salary_dashboard, name="salary_dashboard"),
    path("principal/salaries/add/", views.salary_payment_create, name="salary_payment_create"),
    path("principal/transport/", views.transport_list, name="transport_list"),
    path("principal/transport/add/", views.transport_create, name="transport_create"),
    path("principal/transport/payments/add/", views.transport_payment_create, name="transport_payment_create"),
    path("principal/exams/", views.exam_list, name="exam_list"),
    path("principal/exams/add/", views.exam_create, name="exam_create"),
    path("principal/results/add/", views.result_create, name="result_create"),
    path("my-results/", views.student_results, name="student_results"),
]
