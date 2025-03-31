# Generated by Django 5.1.7 on 2025-03-27 04:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='DumpRawData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_number', models.IntegerField()),
                ('project_name', models.TextField(null=True)),
                ('project_ID', models.TextField(null=True)),
                ('category', models.TextField(null=True)),
                ('project_description', models.TextField(blank=True, null=True)),
                ('location', models.TextField(null=True)),
                ('municipality', models.TextField(null=True)),
                ('office', models.TextField(null=True)),
                ('year', models.IntegerField(null=True)),
                ('fund', models.TextField(null=True)),
                ('project_cost', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('contract_cost', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('cd', models.IntegerField(blank=True, null=True)),
                ('ntp_date', models.DateField(blank=True, null=True)),
                ('extension', models.IntegerField(blank=True, null=True)),
                ('target_completion_date', models.DateField(blank=True, null=True)),
                ('revised_completion_date', models.CharField(blank=True, max_length=50, null=True)),
                ('date_completed', models.DateField(blank=True, null=True)),
                ('quarter', models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ('total_cost_incured_to_date', models.TextField(blank=True, null=True)),
                ('procurement', models.TextField(blank=True, null=True)),
                ('remarks', models.TextField(null=True)),
                ('project_contractor', models.TextField(null=True)),
                ('tin_number', models.TextField(null=True)),
                ('reason', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FundSource',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fund', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Municipality',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('municipality', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Office',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('office', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Remark',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('remark', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('sub_category', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Year',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('year', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='AddProjectHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('project_number', models.IntegerField()),
                ('project_name', models.TextField(null=True)),
                ('project_ID', models.TextField(null=True)),
                ('category', models.TextField(null=True)),
                ('project_description', models.TextField(blank=True, null=True)),
                ('location', models.TextField(null=True)),
                ('municipality', models.TextField(null=True)),
                ('office', models.TextField(null=True)),
                ('year', models.IntegerField(null=True)),
                ('fund', models.TextField(null=True)),
                ('project_cost', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('contract_cost', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('cd', models.IntegerField(blank=True, null=True)),
                ('ntp_date', models.DateField(blank=True, null=True)),
                ('extension', models.IntegerField(blank=True, null=True)),
                ('target_completion_date', models.DateField(blank=True, null=True)),
                ('revised_completion_date', models.CharField(blank=True, max_length=50, null=True)),
                ('date_completed', models.DateField(blank=True, null=True)),
                ('quarter', models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ('total_cost_incured_to_date', models.TextField(blank=True, null=True)),
                ('procurement', models.TextField(blank=True, null=True)),
                ('remarks', models.TextField(null=True)),
                ('project_contractor', models.TextField(null=True)),
                ('tin_number', models.TextField(null=True)),
                ('reason', models.TextField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('project_number', models.AutoField(primary_key=True, serialize=False)),
                ('project_name', models.TextField()),
                ('project_ID', models.TextField(blank=True, null=True)),
                ('project_description', models.TextField(blank=True, null=True)),
                ('location', models.TextField(blank=True, null=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='home.category')),
                ('fund', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='home.fundsource')),
                ('municipality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='home.municipality')),
                ('office', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.office')),
                ('sub_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='home.subcategory')),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='home.year')),
            ],
            options={
                'ordering': ['project_number'],
            },
        ),
        migrations.CreateModel(
            name='ProjectTimeline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cd', models.IntegerField(blank=True, null=True)),
                ('ntp_date', models.DateField(blank=True, null=True)),
                ('extension', models.IntegerField(blank=True, null=True)),
                ('target_completion_date', models.DateField(blank=True, null=True)),
                ('revised_completion_date', models.CharField(blank=True, max_length=50, null=True)),
                ('total_cost_incurred_to_date', models.CharField(blank=True, max_length=50, null=True)),
                ('date_completed', models.DateField(blank=True, null=True)),
                ('reason', models.TextField(blank=True, null=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='timeline', to='home.project')),
            ],
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('contract_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('procurement', models.TextField(blank=True, null=True)),
                ('project_contractor', models.TextField(blank=True, null=True)),
                ('tin_number', models.TextField(blank=True, null=True)),
                ('quarter', models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='home.project')),
                ('remarks', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='home.remark')),
            ],
        ),
        migrations.CreateModel(
            name='UpdateHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=100)),
                ('old_value', models.TextField(blank=True, null=True)),
                ('new_value', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.project')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
