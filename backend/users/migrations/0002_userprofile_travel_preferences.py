# Generated by Django 5.1.7 on 2025-03-22 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='travel_preferences',
            field=models.TextField(blank=True, help_text="User's travel preferences in their own words", null=True),
        ),
    ]
