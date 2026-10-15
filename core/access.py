from students.models import Student
from .models import TeacherAssignment, StaffMember

def student_for_user(user):
    """Resolve only the Student linked to this authenticated account."""
    try:
        profile = user.student_profile
    except Student.DoesNotExist:
        profile = None
    if profile is not None:
        return profile
    # Backward compatibility for older accounts whose username was admission number.
    return Student.objects.filter(admission_number=user.username, is_active=True).first()

def teacher_assignments(user, permission=None):
    qs = TeacherAssignment.objects.filter(staff__user=user, staff__is_active=True)
    if permission:
        qs = qs.filter(**{permission: True})
    return qs

def students_for_teacher(user, permission=None):
    assignments = teacher_assignments(user, permission)
    from django.db.models import Q
    allowed = Q(pk__in=[])
    for a in assignments:
        allowed |= Q(student_class=a.student_class, section=a.section)
    return Student.objects.filter(allowed, is_active=True)

def teacher_has_permission(user, permission):
    return teacher_assignments(user, permission).exists()
