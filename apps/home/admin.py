# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin

# Register your models here.
from .models import (
    Category, Year, Municipality, Remark, FundSource, Office,
    Project, Contract, ProjectTimeline
)

# ===================== Foreign Key Models ===================== #

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category')
    search_fields = ('category',)

@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('id', 'year')
    search_fields = ('year',)

@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('id', 'municipality')
    search_fields = ('municipality',)

@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'remark')
    search_fields = ('remark',)

@admin.register(FundSource)
class FundSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'fund')
    search_fields = ('fund',)

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('id', 'office')
    search_fields = ('office',)

# ===================== Main Tables ===================== #

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_number', 'project_name', 'category', 'municipality', 'year', 'office', 'fund')
    search_fields = ('project_number', 'project_name', 'project_ID')
    list_filter = ('category', 'municipality', 'year', 'office', 'fund')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('project', 'project_cost', 'contract_cost', 'project_contractor', 'tin_number', 'remarks')
    search_fields = ('project__project_name', 'project_contractor')
    list_filter = ('project_contractor', 'tin_number','remarks')

@admin.register(ProjectTimeline)
class ProjectTimelineAdmin(admin.ModelAdmin):
    list_display = ('project', 'ntp_date', 'target_completion_date', 'revised_completion_date', 'date_completed')
    search_fields = ('project__project_name',)
    list_filter = ('ntp_date', 'target_completion_date', 'date_completed')
