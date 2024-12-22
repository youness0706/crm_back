# Generated by Django 5.1.3 on 2024-12-22 08:14

import ckeditor.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Addedpay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('desc', models.TextField(blank=True)),
                ('amount', models.FloatField()),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Costs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost', models.CharField(max_length=100)),
                ('desc', models.TextField(blank=True)),
                ('amount', models.FloatField()),
                ('date', models.DateTimeField()),
                ('is_allways', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='اسم الجمعية', max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('established_date', models.DateField(blank=True, null=True)),
                ('rent_amount', models.FloatField(default=0)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('datepay', models.DateField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Trainer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, upload_to='photos/%Y/%M/%d')),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('birth_day', models.DateField()),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('phone_parent', models.CharField(max_length=15)),
                ('email', models.CharField(max_length=255)),
                ('CIN', models.CharField(blank=True, max_length=15)),
                ('address', models.CharField(blank=True, max_length=15)),
                ('male_female', models.CharField(choices=[('male', 'male'), ('female', 'female')], default='female', max_length=11)),
                ('belt_degree', models.CharField(choices=[('أبيض', 'أبيض'), ('أبيض مع شريط أصفر', 'أبيض مع شريط أصفر'), ('أصفر', 'أصفر'), ('أصفر مع شريط أخضر', 'أصفر مع شريط أخضر'), ('أخضر', 'أخضر'), ('أخضر مع شريط أزرق', 'أخضر مع شريط أزرق'), ('أزرق', 'أزرق'), ('أزرق مع شريط أحمر', 'أزرق مع شريط أحمر'), ('أحمر', 'أحمر'), ('أحمر مع شريط أسود', 'أحمر مع شريط أسود'), ('أسود', 'أسود')], max_length=50, null=True)),
                ('Degree', models.CharField(max_length=80, null=True)),
                ('category', models.CharField(choices=[('small', 'الصغار'), ('med', 'فتيان'), ('big', 'كبار'), ('women', 'نساء')], default='small', max_length=9)),
                ('tall', models.FloatField(blank=True)),
                ('weight', models.FloatField(blank=True)),
                ('started_day', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=100)),
                ('is_admin', models.BooleanField(default=False)),
                ('started', models.DateField(blank=True)),
                ('salary', models.FloatField(default=0)),
                ('datepay', models.DateField(blank=True, default=django.utils.timezone.now)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=15)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Payments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paymentdate', models.DateField(default=django.utils.timezone.now)),
                ('paymentCategry', models.CharField(choices=[('month', 'شهرية'), ('subscription', 'انخراط'), ('assurance', 'التأمين')], default=True, max_length=20)),
                ('paymentAmount', models.IntegerField(default=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainers.trainer')),
            ],
        ),
        migrations.CreateModel(
            name='Emailed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateField(default=django.utils.timezone.now)),
                ('email', models.CharField(blank=True, max_length=3000)),
                ('category', models.CharField(default='monthly', max_length=300)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainers.trainer')),
            ],
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('title', models.CharField(max_length=200)),
                ('location', models.CharField(default='اركانة نجوم اركانة', max_length=500)),
                ('content', ckeditor.fields.RichTextField()),
                ('category', models.CharField(choices=[('League', 'League'), ('training', 'training'), ('dawri', 'dawri'), ('test', 'test')], max_length=30)),
                ('area', models.CharField(choices=[('local', 'local'), ('reigion', 'reigion'), ('national', 'national')], max_length=30)),
                ('costs', models.FloatField(blank=True)),
                ('participetion_price', models.FloatField(blank=True)),
                ('trainees', models.ManyToManyField(blank=True, to='trainers.trainer')),
            ],
        ),
    ]
