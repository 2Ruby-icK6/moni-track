# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources

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

# ===================== Export =========================== #
# Create export resource classes
class ProjectResource(resources.ModelResource):
    class Meta:
        model = Project

class ContractResource(resources.ModelResource):
    class Meta:
        model = Contract

class ProjectTimelineResource(resources.ModelResource):
    class Meta:
        model = ProjectTimeline

# ===================== Main Tables ===================== #

@admin.register(Project)
class ProjectAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('project_number', 'project_name', 'category', 'municipality', 'year', 'office', 'fund')
    search_fields = ('project_number', 'project_name', 'project_ID')
    list_filter = ('category', 'municipality', 'year', 'office', 'fund')
    resource_class = ProjectResource


@admin.register(Contract)
class ContractAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('project', 'project_cost', 'contract_cost', 'project_contractor', 'tin_number', 'remarks')
    search_fields = ('project__project_name', 'project_contractor')
    list_filter = ('project_contractor', 'tin_number','remarks')
    resource_class = ContractResource

@admin.register(ProjectTimeline)
class ProjectTimelineAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('project', 'ntp_date', 'target_completion_date', 'revised_completion_date', 'date_completed')
    search_fields = ('project__project_name',)
    list_filter = ('ntp_date', 'target_completion_date', 'date_completed')
    resource_class = ProjectTimelineResource