from django.contrib.auth.decorators import login_required, user_passes_test


def is_principal(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="PRINCIPAL").exists()
    )


def is_teacher_or_principal(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=["PRINCIPAL", "TEACHER"]).exists()
    )


def principal_required(view_func):
    return login_required(user_passes_test(is_principal, login_url="portal")(view_func))


def teacher_or_principal_required(view_func):
    return login_required(user_passes_test(is_teacher_or_principal, login_url="portal")(view_func))


def teacher_permission_required(permission, login_url="portal"):
    """Principal has full access; teacher must have at least one explicit assignment."""
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages
    from .access import teacher_has_permission
    def decorator(view_func):
        @login_required(login_url="login")
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if is_principal(request.user):
                return view_func(request, *args, **kwargs)
            if request.user.groups.filter(name="TEACHER").exists() and teacher_has_permission(request.user, permission):
                return view_func(request, *args, **kwargs)
            messages.error(request, "Principal ne is module/class ka access assign nahi kiya hai.")
            return redirect(login_url)
        return _wrapped
    return decorator
