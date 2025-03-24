# Generated by Django 3.2.6 on 2025-03-24 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_rename_contractor_dumprawdata_project_contractor'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddProjectHistory',
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
    ]
