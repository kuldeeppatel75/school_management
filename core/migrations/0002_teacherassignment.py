from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        ('students', '0003_student_user'),
    ]
    operations = [
        migrations.CreateModel(
            name='TeacherAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_class', models.CharField(max_length=30)),
                ('section', models.CharField(max_length=10)),
                ('can_attendance', models.BooleanField(default=True)),
                ('can_exams', models.BooleanField(default=False)),
                ('can_fees', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='core.staffmember')),
            ],
            options={'ordering': ['student_class', 'section', 'staff__full_name']},
        ),
        migrations.AddConstraint(
            model_name='teacherassignment',
            constraint=models.UniqueConstraint(fields=('staff', 'student_class', 'section'), name='unique_teacher_class_section_assignment'),
        ),
    ]
