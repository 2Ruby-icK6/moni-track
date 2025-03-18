# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Base Model table ###############################################################################################################
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

# Foreign table ###############################################################################################################
class Category(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    category = models.TextField(null=False)

    def __str__(self):
        return self.category

class SubCategory(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    sub_category = models.TextField(null=False)

    def __str__(self):
        return self.sub_category

class Year(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    year = models.IntegerField(null=False)

    def __str__(self):
        return str(self.year)


class Municipality(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    municipality = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.municipality


class Remark(models.Model):
    id = models.AutoField(primary_key=True)
    remark = models.CharField(max_length=255, null=False)
    
    def __str__(self):
        return self.remark
    
class Contractor(models.Model):
    id = models.AutoField(primary_key=True)
    contractor = models.TextField(null=True, blank=True)
    tin_number = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.contractor

class FundSource(models.Model):
    id = models.AutoField(primary_key=True)
    fund = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.fund

class Office(models.Model):
    id = models.AutoField(primary_key=True)
    office = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.office

# Normalize table ###############################################################################################################
# Main table ####################################################################################################################
class Project(BaseModel):
    project_number = models.AutoField(primary_key=True)
    project_name = models.TextField(null=False)
    project_ID = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name="infra_views")
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="infra_views")
    project_description = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True, related_name="infra_views")
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name="infra_views")
    fund = models.ForeignKey(FundSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="infra_views")

    class Meta:
        ordering = ['project_number']

# Sub-Main table ################################################################################################################
class Contract(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="contract")
    project_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    contract_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    procurement = models.TextField(null=True, blank=True)
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True, related_name="contract")
    quarter = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    remarks = models.ForeignKey(Remark, on_delete=models.CASCADE, related_name="contract")

class ProjectTimeline(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="timeline")
    cd = models.IntegerField(null=True, blank=True)
    ntp_date = models.DateField(null=True, blank=True)
    extension = models.IntegerField(null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    revised_completion_date = models.CharField(max_length=50, null=True, blank=True)
    date_completed = models.DateField(null=True, blank=True)
