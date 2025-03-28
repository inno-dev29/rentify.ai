# Generated by Django 5.1.7 on 2025-03-22 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('icon', models.CharField(blank=True, help_text='Icon identifier', max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Amenity',
                'verbose_name_plural': 'Amenities',
            },
        ),
        migrations.CreateModel(
            name='PropertyImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='property_images')),
                ('caption', models.CharField(blank=True, max_length=200, null=True)),
                ('is_primary', models.BooleanField(default=False, help_text='Is this the primary property image')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Property Image',
                'verbose_name_plural': 'Property Images',
                'ordering': ['-is_primary', 'upload_date'],
            },
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('property_type', models.CharField(choices=[('house', 'House'), ('apartment', 'Apartment'), ('condo', 'Condominium'), ('townhouse', 'Townhouse'), ('villa', 'Villa'), ('cabin', 'Cabin'), ('other', 'Other')], default='house', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending Approval'), ('archived', 'Archived')], default='pending', max_length=20)),
                ('address_line1', models.CharField(max_length=100)),
                ('address_line2', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(max_length=50)),
                ('state', models.CharField(max_length=50)),
                ('postal_code', models.CharField(max_length=20)),
                ('country', models.CharField(max_length=50)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('bedroom_count', models.PositiveIntegerField(default=1)),
                ('bathroom_count', models.DecimalField(decimal_places=1, default=1.0, max_digits=3)),
                ('max_guests', models.PositiveIntegerField(default=2)),
                ('square_feet', models.PositiveIntegerField(blank=True, null=True)),
                ('base_price', models.DecimalField(decimal_places=2, help_text='Base price per night', max_digits=10)),
                ('cleaning_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('service_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('extra_guest_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('min_nights', models.PositiveIntegerField(default=1)),
                ('house_rules', models.TextField(blank=True, null=True)),
                ('cancellation_policy', models.TextField(blank=True, null=True)),
                ('check_in_time', models.TimeField(blank=True, null=True)),
                ('check_out_time', models.TimeField(blank=True, null=True)),
                ('llm_summary', models.TextField(blank=True, help_text='Property summary generated by LLM', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amenities', models.ManyToManyField(related_name='properties', to='properties.amenity')),
            ],
            options={
                'verbose_name': 'Property',
                'verbose_name_plural': 'Properties',
                'ordering': ['-created_at'],
            },
        ),
    ]
