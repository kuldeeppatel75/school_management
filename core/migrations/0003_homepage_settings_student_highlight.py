from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_teacherassignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hero_title', models.CharField(default='Ramnarayan Yadav School, Khirkia', max_length=180)),
                ('hero_subtitle', models.CharField(default='A better school day.', max_length=240)),
                ('hero_description', models.TextField(blank=True, default='Student records, attendance, fee tracking and academic results — organized in one secure school management portal.', max_length=700)),
                ('hero_image', models.ImageField(blank=True, null=True, upload_to='school/hero/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Homepage settings', 'verbose_name_plural': 'Homepage settings'},
        ),
        migrations.CreateModel(
            name='StudentHighlight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=150)),
                ('caption', models.CharField(help_text='For example: Class 10 topper — 94%', max_length=220)),
                ('photo', models.ImageField(upload_to='school/student-highlights/')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_published', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['display_order', '-created_at']},
        ),
    ]
