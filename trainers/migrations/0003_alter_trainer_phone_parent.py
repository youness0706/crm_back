# Generated by Django 5.1.3 on 2024-12-22 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0002_alter_trainer_phone_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainer',
            name='phone_parent',
            field=models.IntegerField(blank=True),
        ),
    ]
