# Generated by Django 3.2.6 on 2025-03-23 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_alter_projecttimeline_revised_completion_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projecttimeline',
            name='revised_completion_date',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
