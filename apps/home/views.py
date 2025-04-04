# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.forms import inlineformset_factory
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.db import connection, models
from django.forms import modelformset_factory
from django.utils.dateparse import parse_date
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.views import View
from django.views.generic import ListView, FormView, DeleteView
from django.db.models import Count

import openpyxl
import os
import re
import json
from datetime import datetime

from utils.data_utils import excel_to_json, format_date_or_text, get_or_create_foreign_key, compare_project_fields, compare_contract_fields, compare_timeline_fields
from django.utils.decorators import method_decorator
from .decorators import unauthorized_user, allowed_user, admin_only

#------------- Models -------------#
# Main table
from .models import Project, Contract, ProjectTimeline, DumpRawData
# Foreign table
from .models import Category, SubCategory, Municipality, Year, Office, FundSource, Remark
# History Table
from .models import UpdateHistory, AddProjectHistory

#------------- Forms -------------#
# Auth Form
from apps.authentication.forms import UpdateForm, ProjectForm, ProjectTimelineForm, ContractForm, UploadFileForm
from apps.authentication.forms import ProfileUpdateForm, PasswordUpdateForm, UserCreateForm, UserRoleForm
from apps.authentication.forms import FundSourceForm, CategoryForm, SubCategoryForm ,OfficeForm, YearForm

#------------- Login -------------#
@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


#------------- Projects Dashboard -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor', 'Viewer']), name='dispatch')
class ProjectListView(ListView):
    model = Project
    template_name = 'home/dashboard.html'
    context_object_name = 'projects'
    paginate_by = 5

    def get_queryset(self):
        queryset = Project.objects.select_related("timeline", "contract", "contract__remarks").all()
        
        # Get filter parameters from request
        category = self.request.GET.get('category')
        fund = self.request.GET.get('fund')
        municipality = self.request.GET.get('municipality')
        office = self.request.GET.get('office')
        sub_category = self.request.GET.get('sub_category')
        start_year = self.request.GET.get("start_year", "")
        end_year = self.request.GET.get("end_year", "")
        remark = self.request.GET.get('remarks', "")
        search_query = self.request.GET.get("search", "")

        # Apply filters dynamically
        if category:
            queryset = queryset.filter(category__category=category)
        if fund:
            queryset = queryset.filter(fund__fund=fund)
        if municipality:
            queryset = queryset.filter(municipality__municipality=municipality)
        if office:
            queryset = queryset.filter(office__office=office)
        if sub_category:
            queryset = queryset.filter(sub_category__sub_category=sub_category)
        if start_year and end_year:
            queryset = queryset.filter(year__year__range=(start_year, end_year))
        if remark:
            queryset = queryset.filter(contract__remarks__remark=remark)
        
        # Search functionality
        if search_query:
            queryset = queryset.filter(
                Q(project_number__icontains=search_query) |
                Q(project_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtered_queryset = self.get_queryset()
        context['total_results'] = filtered_queryset.count()

        context['category'] = Category.objects.values_list('category', flat=True).distinct().order_by('category')
        context['fund'] = FundSource.objects.values_list('fund', flat=True).distinct().order_by('fund')
        context['municipality'] = Municipality.objects.values_list('municipality', flat=True).distinct().order_by('municipality')
        context['office'] = Office.objects.values_list('office', flat=True).distinct().order_by('office')
        context['sub_category'] = SubCategory.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        context['remark'] = Remark.objects.values_list('remark', flat=True).distinct().order_by('remark')
        context['year'] = Year.objects.values_list('year', flat=True).distinct().order_by('year')
        context['page_title'] = "Dashboard"
        return context

# API View for Chart Data
def project_chart_data(request):
    projects_per_year = (
        Project.objects.values("year__year")  # Correct reference to Year model
        .annotate(count=Count("project_number"))  # Count projects per year
        .order_by("year__year")
    )

    labels = [entry["year__year"] for entry in projects_per_year if entry["year__year"] is not None]
    data = [entry["count"] for entry in projects_per_year if entry["year__year"] is not None]

    return JsonResponse({"labels": labels, "data": data})

#------------- Projects Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor', 'Viewer']), name='dispatch')
class ProjectTableView(ListView):
    model = Project
    template_name = 'home/tables.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.select_related("timeline", "contract", "contract__remarks").all()
        
        # Get filter parameters from request
        category = self.request.GET.get('category')
        fund = self.request.GET.get('fund')
        municipality = self.request.GET.get('municipality')
        office = self.request.GET.get('office')
        sub_category = self.request.GET.get('sub_category')
        start_year = self.request.GET.get("start_year", "")
        end_year = self.request.GET.get("end_year", "")
        remark = self.request.GET.get('remarks', "")
        search_query = self.request.GET.get("search", "")

        # Apply filters dynamically
        if category:
            queryset = queryset.filter(category__category=category)
        if fund:
            queryset = queryset.filter(fund__fund=fund)
        if municipality:
            queryset = queryset.filter(municipality__municipality=municipality)
        if office:
            queryset = queryset.filter(office__office=office)
        if sub_category:
            queryset = queryset.filter(sub_category__sub_category=sub_category)
        if start_year and end_year:
            queryset = queryset.filter(year__year__range=(start_year, end_year))
        if remark:
            queryset = queryset.filter(contract__remarks__remark=remark)
        
        # Search functionality
        if search_query:
            queryset = queryset.filter(
                Q(project_number__icontains=search_query) |
                Q(project_name__icontains=search_query)
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtered_queryset = self.get_queryset()
        context['total_results'] = filtered_queryset.count()

        # Pass available filter options to the template
        context['category'] = Category.objects.values_list('category', flat=True).distinct().order_by('category')
        context['fund'] = FundSource.objects.values_list('fund', flat=True).distinct().order_by('fund')
        context['municipality'] = Municipality.objects.values_list('municipality', flat=True).distinct().order_by('municipality')
        context['office'] = Office.objects.values_list('office', flat=True).distinct().order_by('office')
        context['sub_category'] = SubCategory.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        context['year'] = Year.objects.values_list('year', flat=True).distinct().order_by('year')
        context['remark'] = Remark.objects.values_list('remark', flat=True).distinct().order_by('remark')
        context['show_search_table'] = True
        context['show_search_flextable'] = False
        context['page_title'] = "Infracstructure Table"

        # Pass selected filters to the template for form repopulation
        context['selected_filters'] = {
            'category': self.request.GET.get('category', ''),
            'fund': self.request.GET.get('fund', ''),
            'municipality': self.request.GET.get('municipality', ''),
            'office': self.request.GET.get('office', ''),
            'sub_category': self.request.GET.get('sub_category', ''),
            'year': self.request.GET.get('year', ''),
            'remark': self.request.GET.get('remarks', ''),
        }
        
        return context
    
#------------- Projects Flex Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor', 'Viewer']), name='dispatch')
class ProjectFlexTableView(ListView):
    model = Project
    template_name = "home/flex-tables.html"
    context_object_name = "projects"
    paginate_by = 15

    def get_queryset(self):
        queryset = Project.objects.select_related("timeline", "contract", "contract__remarks").annotate(
            # Project Timeline
            cd=F("timeline__cd"),
            ntp_date=F("timeline__ntp_date"),
            extension=F("timeline__extension"),
            target=F("timeline__target_completion_date"),
            revised=F("timeline__revised_completion_date"),
            date_completed=F("timeline__date_completed"),
            total_cost=F("timeline__total_cost_incurred_to_date"),
            reason=F("timeline__reason"),

            # Contract 
            project_cost=F("contract__project_cost"),
            contract_cost=F("contract__contract_cost"),
            procurement=F("contract__procurement"),
            quarter=F("contract__quarter"),
            remarks=F("contract__remarks__remark"),
            contractor=F("contract__project_contractor"),
            tin_number=F("contract__tin_number"),
        ).order_by("project_number")

        # Get filter parameters from request
        category = self.request.GET.get("category", "")
        sub_category = self.request.GET.get("sub_category", "")
        municipality = self.request.GET.get("municipality", "")
        start_year = self.request.GET.get("start_year", "")
        end_year = self.request.GET.get("end_year", "")
        fund = self.request.GET.get("fund", "")
        remarks = self.request.GET.get("remarks", "")
        search_query = self.request.GET.get("search", "")

        # Apply filters
        if category:
            queryset = queryset.filter(category__category=category)
        if sub_category:
            queryset = queryset.filter(sub_category__sub_category=sub_category)
        if municipality:
            queryset = queryset.filter(municipality__municipality=municipality)
        if start_year and end_year:
            queryset = queryset.filter(year__year__range=(start_year, end_year))
        if fund:
            queryset = queryset.filter(fund__fund=fund)
        if remarks:
            queryset = queryset.filter(contract__remarks__remark=remarks)
        
        # Search functionality
        if search_query:
            queryset = queryset.filter(
                Q(project_number__icontains=search_query) |
                Q(project_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtered_queryset = self.get_queryset()
        context['total_results'] = filtered_queryset.count()
        
        column_display_names = {
            "project_number": "NO",
            "project_name": "Project Name",
            "project_ID": "Project ID",
            "category": "Category",
            "sub_category": "Sub Category",
            "project_description": "Project Description",
            "location": "Location",
            "municipality": "Municipality",
            "office": "Implementing Office",
            "year": "Project Year",
            "fund": "Source of Fund",
            "project_cost": "Project Cost",
            "contract_cost": "Contract Cost",
            "cd": "C D",
            "ntp_date": "NTP Date",
            "extension": "NO of Extension",
            "target": "Target Completion Date",
            "revised": "Revised Completion Date",
            "date_completed": "Date Completed",
            "quarter": "Quarter",
            "total_cost": "Total Cost Incurred to Date",
            "procurement": "Mode of Procurement",
            "remarks": "General Remarks",
            "contractor": "Project Contractor",
            "tin_number": "Tin Number",
            "reason": "Reason",
        }

        context.update({
            "column_list": list(column_display_names.keys()),
            "column_display_names": column_display_names,
            "category": Category.objects.values_list("category", flat=True).order_by("category"),
            "fund": FundSource.objects.values_list("fund", flat=True).order_by("fund"),
            "municipality": Municipality.objects.values_list("municipality", flat=True).order_by("municipality"),
            "office": Office.objects.values_list("office", flat=True).order_by("office"),
            "sub_category": SubCategory.objects.values_list("sub_category", flat=True).order_by("sub_category"),
            "year": Year.objects.values_list("year", flat=True).order_by("year"),
            "remark": Remark.objects.values_list("remark", flat=True).order_by("remark"),
            "selected_filters": self.request.GET,
            "show_search_table": False,  # Change based on logic
            "show_search_flextable": True,  # Change based on logic
            "page_title": "Flex Table"
        })

        return context
    
#------------- Download Table Preview -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class DonwloadTablePreview(ListView):
    model = Project
    template_name = "crud/file/download-file.html"
    context_object_name = "projects"
    paginate_by = 15

    def get_queryset(self):
        queryset = Project.objects.select_related("timeline", "contract", "contract__remarks").annotate(
            # Project Timeline
            cd=F("timeline__cd"),
            ntp_date=F("timeline__ntp_date"),
            extension=F("timeline__extension"),
            target=F("timeline__target_completion_date"),
            revised=F("timeline__revised_completion_date"),
            date_completed=F("timeline__date_completed"),
            total_cost=F("timeline__total_cost_incurred_to_date"),
            reason=F("timeline__reason"),

            # Contract 
            project_cost=F("contract__project_cost"),
            contract_cost=F("contract__contract_cost"),
            procurement=F("contract__procurement"),
            quarter=F("contract__quarter"),
            remarks=F("contract__remarks__remark"),
            contractor=F("contract__project_contractor"),
            tin_number=F("contract__tin_number"),
        ).order_by("project_number")

        # Get filter parameters from request
        category = self.request.GET.get("category", "")
        sub_category = self.request.GET.get("sub_category", "")
        municipality = self.request.GET.get("municipality", "")
        start_year = self.request.GET.get("start_year", "")
        end_year = self.request.GET.get("end_year", "")
        fund = self.request.GET.get("fund", "")
        remarks = self.request.GET.get("remarks", "")

        # Apply filters
        if category:
            queryset = queryset.filter(category__category=category)
        if sub_category:
            queryset = queryset.filter(sub_category__sub_category=sub_category)
        if municipality:
            queryset = queryset.filter(municipality__municipality=municipality)
        if start_year and end_year:
            queryset = queryset.filter(year__year__range=(start_year, end_year))
        if fund:
            queryset = queryset.filter(fund__fund__icontains=fund)
        if remarks:
            queryset = queryset.filter(contract__remarks__remark=remarks)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtered_queryset = self.get_queryset()
        context['total_results'] = filtered_queryset.count()
        context['page_title'] = "Download"
        
        column_display_names = {
            "project_number": "NO",
            "project_name": "Project Name",
            "project_ID": "Project ID",
            "category": "Category",
            "sub_category": "Sub Category",
            "project_description": "Project Description",
            "location": "Location",
            "municipality": "Municipality",
            "office": "Implementing Office",
            "year": "Project Year",
            "fund": "Source of Fund",
            "project_cost": "Project Cost",
            "contract_cost": "Contract Cost",
            "cd": "C D",
            "ntp_date": "NTP Date",
            "extension": "NO of Extension",
            "target": "Target Completion Date",
            "revised": "Revised Completion Date",
            "date_completed": "Date Completed",
            "quarter": "Quarter",
            "total_cost": "Total Cost Incurred to Date",
            "procurement": "Mode of Procurement",
            "remarks": "General Remarks",
            "contractor": "Project Contractor",
            "tin_number": "Tin Number",
            "reason": "Reason",
        }

        context.update({
            "column_list": list(column_display_names.keys()),
            "column_display_names": column_display_names,
            "category": Category.objects.values_list("category", flat=True).order_by("category"),
            "fund": FundSource.objects.values_list("fund", flat=True).order_by("fund"),
            "municipality": Municipality.objects.values_list("municipality", flat=True).order_by("municipality"),
            "office": Office.objects.values_list("office", flat=True).order_by("office"),
            "sub_category": SubCategory.objects.values_list("sub_category", flat=True).order_by("sub_category"),
            "year": Year.objects.values_list("year", flat=True).order_by("year"),
            "remark": Remark.objects.values_list("remark", flat=True).order_by("remark"),
            "selected_filters": self.request.GET,
        })

        return context

def export_data(request):
    """Exports Project, Contract, and Timeline data into a pre-formatted Excel file with filters"""

    # Get filter parameters from request
    category_filter = request.GET.get('category', None)
    subcategory_filter = request.GET.get('sub_category', None)
    municipality_filter = request.GET.get('municipality', None)
    fund_filter = request.GET.get('fund', None)
    remarks_filter = request.GET.get('remarks', None)
    start_year_filter = request.GET.get('start_year', None)
    end_year_filter = request.GET.get('end_year', None)

    # Start with all projects
    projects = Project.objects.all()

    # Apply filters
    if category_filter:
        projects = projects.filter(category__category=category_filter)
    if subcategory_filter:
        projects = projects.filter(sub_category__sub_category=subcategory_filter)
    if municipality_filter:
        projects = projects.filter(municipality__municipality=municipality_filter)
    if fund_filter:
        projects = projects.filter(fund__fund=fund_filter)
    if remarks_filter:
        projects = projects.filter(contract__remarks__remark=remarks_filter)
    if start_year_filter and end_year_filter:
        projects = projects.filter(year__year__range=(start_year_filter, end_year_filter))

    # Load the pre-formatted Excel template
    template_path = os.path.join(settings.CORE_DIR, 'apps','static', 'templates', 'export_template.xlsx')  # Update path
    workbook = openpyxl.load_workbook(template_path)
    sheet = workbook.active  # Modify this if needed

    start_row = 4  # Ensure this matches where data should start in the template

    for project in projects:
        contract = Contract.objects.filter(project=project).first()
        timeline = ProjectTimeline.objects.filter(project=project).first()

        # Write data to the correct columns
        sheet[f"A{start_row}"] = project.project_number  # NO.
        sheet[f"B{start_row}"] = project.project_name  # PROJECT NAME
        sheet[f"C{start_row}"] = project.project_ID  # PROJECT ID
        sheet[f"D{start_row}"] = project.category.category if project.category else None  # PPDO CATEGORY
        sheet[f"E{start_row}"] = project.sub_category.sub_category if project.sub_category else None  # SUB CATEGORY
        sheet[f"F{start_row}"] = project.project_description  # PROJECT DESCRIPTION
        sheet[f"G{start_row}"] = project.location  # LOCATION
        sheet[f"H{start_row}"] = project.municipality.municipality if project.municipality else None  # MUNICIPALITY
        sheet[f"I{start_row}"] = project.office.office if project.office else None  # IMPLEMENTING OFFICE
        sheet[f"J{start_row}"] = project.year.year if project.year else None  # YEAR
        sheet[f"K{start_row}"] = project.fund.fund if project.fund else None  # SOURCE OF FUND
        sheet[f"L{start_row}"] = contract.project_cost if contract else None  # PROJECT COST
        sheet[f"M{start_row}"] = contract.contract_cost if contract else None  # CONTRACT COST
        sheet[f"N{start_row}"] = timeline.cd if timeline else None  # C.D
        sheet[f"O{start_row}"] = timeline.ntp_date.strftime('%Y-%m-%d') if timeline and timeline.ntp_date else None  # NTP DATE
        sheet[f"P{start_row}"] = timeline.extension if timeline else None  # NO. OF EXTENSION
        sheet[f"R{start_row}"] = format_date_or_text(timeline.revised_completion_date) if timeline else None  # REVISED COMPLETION DATE
        sheet[f"S{start_row}"] = format_date_or_text(timeline.date_completed) if timeline else None  # DATE COMPLETED
        sheet[f"Q{start_row}"] = format_date_or_text(timeline.target_completion_date) if timeline else None  # TARGET COMPLETION DATE
        sheet[f"T{start_row}"] = contract.quarter if contract else None  # AS OF MONTH YEAR
        sheet[f"U{start_row}"] = timeline.total_cost_incurred_to_date if timeline else None  # TOTAL COST INCURRED TO DATE
        sheet[f"V{start_row}"] = contract.procurement if contract else None  # MODE OF PROCUREMENT
        sheet[f"W{start_row}"] = contract.remarks.remark if contract and contract.remarks else None  # GENERAL REMARKS
        sheet[f"X{start_row}"] = contract.project_contractor if contract else None  # PROJECT CONTRACTOR
        sheet[f"Y{start_row}"] = contract.tin_number if contract else None  # TIN NUMBER
        sheet[f"Z{start_row}"] = timeline.reason if timeline else None  # REASON

        start_row += 1  # Move to the next row

    # Create response for downloading the file
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")  # Format: YYYY-MM-DD HH:MM AM/PM
    response["Content-Disposition"] = f'attachment; filename="Exported_File{now}.xlsx"'

    # Save workbook to response
    workbook.save(response)

    return response

#------------- Udpate Project -------------#
# Create inline formsets for ProjectTimeline and Contract
ProjectTimelineFormSet = inlineformset_factory(Project, ProjectTimeline, form=ProjectTimelineForm, extra=0, can_delete=True)
ContractFormSet = inlineformset_factory(Project, Contract, form=ContractForm, extra=0, can_delete=True)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class UpdateDataView(View):
    template_name = 'crud/update-infra.html'

    def get(self, request):
        query_project_number = request.GET.get('search_project_number', '').strip()
        query_project_name = request.GET.get('search_project_name', '').strip()
        
        projects = Project.objects.all()
        project = None
        form = UpdateForm()
        timeline_formset = ProjectTimelineFormSet()
        contract_formset = ContractFormSet()

        if query_project_number or query_project_name:
            if query_project_number:
                projects = projects.filter(project_number=query_project_number)
            if query_project_name:
                projects = projects.filter(project_name__icontains=query_project_name)

            if projects.count() == 1:
                project = projects.first()
                form = UpdateForm(instance=project)
                timeline_formset = ProjectTimelineFormSet(instance=project)
                contract_formset = ContractFormSet(instance=project)

        return render(request, self.template_name, {
            'projects': projects,
            'form': form,
            'project': project,
            'timeline_formset': timeline_formset,
            'contract_formset': contract_formset,
            "page_title": "Update Infrastructure"
        })

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        # Fetch the original values before update
        original_project = Project.objects.get(pk=pk)
        original_timeline = project.timeline if hasattr(project, 'timeline') else None
        original_contract = project.contract if hasattr(project, 'contract') else None

        
        form = UpdateForm(request.POST, instance=project)
        timeline_formset = ProjectTimelineFormSet(request.POST, instance=project)
        contract_formset = ContractFormSet(request.POST, instance=project)

        if form.is_valid() and timeline_formset.is_valid() and contract_formset.is_valid():
            updated_project = form.save()

            # Track changes for project fields
            for field in form.changed_data:
                old_value = getattr(original_project, field, "")
                new_value = form.cleaned_data[field]
                
                if old_value is None:
                    old_value = None
                if new_value is None:
                    new_value = None
                
                # print(f"Updating '{field}': '{old_value}' -> '{new_value}'")
                UpdateHistory.objects.create(
                    project=project,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                    updated_by=request.user
                )

            # Ensure formsets are properly saved
            timelines = timeline_formset.save(commit=False)
            for timeline in timelines:
                timeline.project = updated_project  # Explicitly set project FK
                timeline.save()
            
            contracts = contract_formset.save(commit=False)
            for contract in contracts:
                contract.project = updated_project  # Explicitly set project FK
                contract.save()
            
            # Fetch the latest saved instances
            updated_timeline = ProjectTimeline.objects.filter(project=project).first()
            updated_contract = Contract.objects.filter(project=project).first()

            # Track changes for timeline
            if original_timeline and updated_timeline:
                for field in ProjectTimeline._meta.fields:
                    field_name = field.name
                    old_value = getattr(original_timeline, field_name, None)
                    new_value = getattr(updated_timeline, field_name, None)

                    # Only log changes if values are different
                    if old_value != new_value:
                        UpdateHistory.objects.create(
                            project=project,
                            field_name=f"Timeline: {field_name}",
                            old_value=old_value if old_value is not None else "None",
                            new_value=new_value if new_value is not None else "None",
                            updated_by=request.user
                        )

            # Track changes for contract
            if original_contract and updated_contract:
                for field in Contract._meta.fields:
                    field_name = field.name
                    old_value = getattr(original_contract, field_name, None)
                    new_value = getattr(updated_contract, field_name, None)

                    # Only log changes if values are different
                    if old_value != new_value:
                        UpdateHistory.objects.create(
                            project=project,
                            field_name=f"Contract: {field_name}",
                            old_value=old_value if old_value is not None else "None",
                            new_value=new_value if new_value is not None else "None",
                            updated_by=request.user
                        )

            # Also delete any removed instances
            timeline_formset.save_m2m()
            contract_formset.save_m2m()

            return redirect('update_data')

        return render(request, self.template_name, {
            'form': form,
            'project': project,
            'timeline_formset': timeline_formset,
            'contract_formset': contract_formset,
            "page_title": "Update Infrastructure"
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Update Infrastructure"

        return context

#------------- Udpate History Project -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class UpdateHistoryView(ListView):
    """
    Displays update history for all users.
    """
    model = UpdateHistory
    template_name = "crud/history/update-history.html"
    context_object_name = "history_entries"
    ordering = ["-updated_at"]

    def get_queryset(self):
        return UpdateHistory.objects.all()  # All users can view history
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Updated History"
        return context

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class UpdateHistoryActionView(View):
    """
    Handles the revert (undo) action. The accept option has been removed.
    """
    def post(self, request, history_id, action):
        history_entry = get_object_or_404(UpdateHistory, id=history_id)

        # Check if the logged-in user is the one who made the update
        if history_entry.updated_by != request.user:
            messages.error(request, "You can only revert your own updates.")
            return redirect("update-history")

        project = history_entry.project
        field_name = history_entry.field_name
        old_value = history_entry.old_value

        # Ensure that if old_value is a string "None", we set it to actual None (null)
        if old_value == "None":
            old_value = None

        if action == "revert":
            # Handling fields in the Project model
            if hasattr(project, field_name):
                setattr(project, field_name, old_value)
                project.save()

            # Handling fields in the Contract model
            elif field_name.startswith("Contract: "):
                contract_field = field_name.replace("Contract: ", "")
                contract = getattr(project, "contract", None)
                if contract and hasattr(contract, contract_field):
                    setattr(contract, contract_field, old_value)
                    contract.save()

            # Handling fields in the ProjectTimeline model
            elif field_name.startswith("Timeline: "):
                timeline_field = field_name.replace("Timeline: ", "")
                timeline = getattr(project, "timeline", None)
                if timeline and hasattr(timeline, timeline_field):
                    setattr(timeline, timeline_field, old_value)
                    timeline.save()

            else:
                messages.error(request, "Invalid field name, unable to revert.")
                return redirect("update-history")

            # Remove the history entry after reverting
            history_entry.delete()
            messages.success(request, f"Reverted {field_name} to '{old_value}'.")

        return redirect("update-history")

#------------- Upload File -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class ImportAndPreviewView(View):
    template_name = "crud/file/import-file.html"

    def get(self, request):
        form = UploadFileForm()
        context = self.get_context_data(request, form)
        return render(request, self.template_name, context)

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES["file"]
            if not file.name.endswith((".xlsx", ".xls")):
                messages.error(request, "Invalid file format. Please upload an Excel file.")
                return redirect("import_file")

            try:
                temp_json_path, data = self.process_file(file)

                if not data:
                    self.cleanup_file(temp_json_path)
                    raise ValueError("Error: The uploaded file is empty or unreadable.")

                quarter_column = self.detect_quarter_column(data)
                if not quarter_column:
                    self.cleanup_file(temp_json_path)
                    raise ValueError("Error: 'Quarter' column not found in the dataset.")
                
                expected_columns = {"NO.", "PROVINCIAL GOVERNMENT OF PALAWAN PROJECT NAME", "PROJECT ID", "PPDO CATEGORY", 
                                    "PROJECT DESCRIPTION", "LOCATION", "MUNICIPALITY", "IMPLEMENTING OFFICE", "YEAR", 
                                    "SOURCE OF FUND", "PROJECT COST", "CONTRACT COST", "C.D", "NTP DATE", "NO. OF EXTENSION", 
                                    "TARGET COMPLETION DATE", "REVISED COMPLETION DATE", "DATE COMPLETED", quarter_column, 
                                    "TOTAL COST INCURED TO DATE", "MODE OF PROCUREMENT", "GENERAL REMARKS", "PROJECT CONTRACTOR", 
                                    "TIN NUMBER", "REASON"}
                file_columns = set(data[0].keys())
                
                if not expected_columns.issubset(file_columns):
                    self.cleanup_file(temp_json_path)
                    raise ValueError("Error: The uploaded file has an incorrect format or missing required columns.")

                errors = self.validate_data(data)
                if errors:
                    self.cleanup_file(temp_json_path)
                    raise ValueError("Data validation failed: " + "; ".join(errors))

                DumpRawData.objects.all().delete()
                self.save_data(data, quarter_column)
                os.remove(temp_json_path)

                messages.success(request, "File uploaded and processed successfully! Preview the data before merging.")
                return redirect("import_file")

            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                return redirect("import_file")

        context = self.get_context_data(request, form)
        return render(request, self.template_name, context)

    def process_file(self, file):
        temp_excel_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(temp_excel_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        temp_json_path = os.path.splitext(temp_excel_path)[0] + ".json"
        try:
            excel_to_json(temp_excel_path, temp_json_path)
            with open(temp_json_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except Exception:
            self.cleanup_file(temp_excel_path, temp_json_path)
            return None, None

        self.cleanup_file(temp_excel_path)
        return temp_json_path, data

    def cleanup_file(self, *file_paths):
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    def detect_quarter_column(self, data):
        for key in data[0].keys():
            if re.search(r"AS OF [A-Z]+ \d{4}", key, re.IGNORECASE):
                return key
        return None

    def validate_data(self, data):
        errors = []
        for index, item in enumerate(data):
            if not item.get("PROVINCIAL GOVERNMENT OF PALAWAN PROJECT NAME"):
                errors.append(f"Row {index + 1}: Project Name is required.")
            if not item.get("YEAR"):
                errors.append(f"Row {index + 1}: Year is required.")
        return errors

    def save_data(self, data, quarter_column):
        for item in data:
            DumpRawData.objects.create(
                project_number=item.get("NO.", ""),
                project_name=item.get("PROVINCIAL GOVERNMENT OF PALAWAN PROJECT NAME", ""),
                project_ID=item.get("PROJECT ID", ""),
                category=item.get("PPDO CATEGORY", ""),
                project_description=item.get("PROJECT DESCRIPTION", ""),
                location=item.get("LOCATION", ""),
                municipality=item.get("MUNICIPALITY", ""),
                office=item.get("IMPLEMENTING OFFICE", ""),
                year=item.get("YEAR", ""),
                fund=item.get("SOURCE OF FUND", ""),
                project_cost=item.get("PROJECT COST", ""),
                contract_cost=item.get("CONTRACT COST", ""),
                cd=item.get("C.D", ""),
                ntp_date=item.get("NTP DATE", ""),
                extension=item.get("NO. OF EXTENSION", ""),
                target_completion_date=item.get("TARGET COMPLETION DATE", ""),
                revised_completion_date=item.get("REVISED COMPLETION DATE", ""),
                date_completed=item.get("DATE COMPLETED", ""),
                quarter=item.get(quarter_column, ""),
                total_cost_incured_to_date=item.get("TOTAL COST INCURED TO DATE", ""),
                procurement=item.get("MODE OF PROCUREMENT", ""),
                remarks=item.get("GENERAL REMARKS", ""),
                project_contractor=item.get("PROJECT CONTRACTOR", ""),
                tin_number=item.get("TIN NUMBER", ""),
                reason=item.get("REASON", ""),
            )

    def get_context_data(self, request, form):
        """Returns context data including paginated records and display names."""
        dump_data = DumpRawData.objects.all().order_by("id")
        paginator = Paginator(dump_data, 10)  # Show 10 rows per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        column_list = [
            "project_number", "project_name", "project_ID", "category",
            "project_description", "location", "municipality", "office", "year",
            "fund", "project_cost", "contract_cost", "cd", "ntp_date", "extension",
            "target_completion_date", "revised_completion_date", "date_completed",
            "quarter", "total_cost_incured_to_date", "procurement", "remarks",
            "project_contractor", "tin_number", "reason"
        ]

        column_display_names = {
            "project_number": "No.",
            "project_name": "PGP Project Name",
            "project_ID": "Project ID",
            "category": "Project Category",
            "project_description": "Project Description",
            "location": "Location",
            "municipality": "Municipality",
            "office": "Implementing Office",
            "year": "Project Year",
            "fund": "Funding Source",
            "project_cost": "Project Cost",
            "contract_cost": "Contract Cost",
            "cd": "Contract Duration",
            "ntp_date": "NTP Date",
            "extension": "Extension",
            "target_completion_date": "Target Completion Date",
            "revised_completion_date": "Revised Completion Date",
            "date_completed": "Date Completed",
            "quarter": "Quarter",
            "total_cost_incured_to_date": "Total Cost Incurred to Date",
            "procurement": "Procurement Mode",
            "remarks": "General Remarks",
            "project_contractor": "Project Contractor",
            "tin_number": "TIN Number",
            "reason": "Reason"
        }

        return {
            "form": form,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "total_results": dump_data.count(),
            "column_list": column_list,
            "column_display_names": column_display_names,
            "page_title": "Import"

        }

def discard_data(request):
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE home_dumprawdata;") 

    messages.success(request, "Imported data has been discarded successfully.")
    return redirect("import_file")

#------------- Merge Preview -------------#
def preview_merge_data(request):
    dump_data = DumpRawData.objects.all()
    changes = []
    new_projects = []
    user = request.user  # Get the logged-in user

    # Foreign key mappings
    category_mapping = {c.category: c for c in Category.objects.all()}
    municipality_mapping = {m.municipality: m for m in Municipality.objects.all()}
    year_mapping = {y.year: y for y in Year.objects.all()}
    fund_mapping = {f.fund: f for f in FundSource.objects.all()}  # Fund source mapping
    remark_mapping = {r.remark: r for r in Remark.objects.all()}
    office_mapping = {o.office: o for o in Office.objects.all()}

    foreign_key_fields = {
        "category": category_mapping,
        "municipality": municipality_mapping,
        "fund": fund_mapping,
        "year": year_mapping,
        "remark": remark_mapping,
        "office": office_mapping,
    }

    for dump_entry in dump_data:
        try:
            main_entry = Project.objects.get(project_number=dump_entry.project_number)
            exists = True
        except Project.DoesNotExist:
            # Auto-create missing foreign keys before project creation
            category = category_mapping.get(dump_entry.category)
            municipality = municipality_mapping.get(dump_entry.municipality)
            office = office_mapping.get(dump_entry.office)
            year = year_mapping.get(dump_entry.year)
            fund = get_or_create_foreign_key(fund_mapping, FundSource, dump_entry.fund, "fund")  # Auto-create fund
            remark = remark_mapping.get(dump_entry.remarks)

            # Create new Project entry
            main_entry = Project.objects.create(
                project_number=dump_entry.project_number,
                project_name=dump_entry.project_name,
                project_ID=dump_entry.project_ID,
                category=category,
                municipality=municipality,
                office=office,
                year=year,
                fund=fund,  # Assign the possibly newly created fund
                project_description=dump_entry.project_description,
                location=dump_entry.location,
            )
            exists = False

            # Create a new Contract entry
            contract_entry = Contract.objects.create(
                project=main_entry,
                project_cost=dump_entry.project_cost,
                contract_cost=dump_entry.contract_cost,
                remarks=remark,
                quarter=dump_entry.quarter,
                project_contractor=dump_entry.project_contractor,
                tin_number=dump_entry.tin_number,
                procurement=dump_entry.procurement,
            )

            # Create a new ProjectTimeline entry
            timeline_entry = ProjectTimeline.objects.create(
                project=main_entry,
                cd=dump_entry.cd,
                ntp_date=dump_entry.ntp_date,
                extension=dump_entry.extension,
                target_completion_date=dump_entry.target_completion_date,
                revised_completion_date=dump_entry.revised_completion_date,
                date_completed=dump_entry.date_completed,
                reason=dump_entry.reason,
                total_cost_incurred_to_date=dump_entry.total_cost_incured_to_date,
            )

            # Log new project in history
            AddProjectHistory.objects.create(
                created_by=user,
                project_number=dump_entry.project_number,
                project_name=dump_entry.project_name,
                project_ID=dump_entry.project_ID,
                category=dump_entry.category,
                project_description=dump_entry.project_description,
                location=dump_entry.location,
                municipality=dump_entry.municipality,
                office=dump_entry.office,
                year=dump_entry.year,
                fund=dump_entry.fund,  # Store fund in history
                project_cost=dump_entry.project_cost,
                contract_cost=dump_entry.contract_cost,
                cd=dump_entry.cd,
                ntp_date=dump_entry.ntp_date,
                extension=dump_entry.extension,
                target_completion_date=dump_entry.target_completion_date,
                revised_completion_date=dump_entry.revised_completion_date,
                date_completed=dump_entry.date_completed,
                quarter=dump_entry.quarter,
                total_cost_incured_to_date=dump_entry.total_cost_incured_to_date,
                procurement=dump_entry.procurement,
                remarks=dump_entry.remarks,
                project_contractor=dump_entry.project_contractor,
                tin_number=dump_entry.tin_number,
                reason=dump_entry.reason,
            )

            # Track new projects
            new_projects.append(main_entry.project_number)

        entry_changes = {
            "project_number": dump_entry.project_number,
            "project_name": dump_entry.project_name,
            "fields": [],
            "exists": exists,
        }

        # If the project is new, mark all fields as new
        if not exists:
            entry_changes["fields"].append({
                "field_name": "New Project",
                "old_value": "-",
                "new_value": "Added",
            })
            changes.append(entry_changes)  # Add new projects to changes
            continue  # Skip field comparisons

        # Compare Project Fields
        project_changes = compare_project_fields(main_entry, dump_entry, foreign_key_fields)
        entry_changes["fields"].extend(project_changes)

        # Compare Contract Fields
        try:
            contract_entry = Contract.objects.get(project=main_entry)
            contract_changes = compare_contract_fields(contract_entry, dump_entry)
            entry_changes["fields"].extend(contract_changes)
        except Contract.DoesNotExist:
            continue

        # Compare Timeline Fields
        try:
            timeline_entry = ProjectTimeline.objects.get(project=main_entry)
            timeline_changes = compare_timeline_fields(timeline_entry, dump_entry)
            entry_changes["fields"].extend(timeline_changes)
        except ProjectTimeline.DoesNotExist:
            continue

        if entry_changes["fields"]:
            changes.append(entry_changes)

    return render(request, "crud/file/merge-preview.html", {"changes": changes, "new_projects": new_projects, "page_title": "Prview Merge Data"})

def merge_selected_data(request):
    if request.method == "POST":
        selected_entries = request.POST.getlist("selected_entries")

        if not selected_entries:
            messages.warning(request, "No entries selected for merging.")
            return redirect("preview_merge_data")

        all_entries = DumpRawData.objects.all()
        process_all = "ALL" in selected_entries  # Check if 'ALL' is selected

        # Correct filtering method
        selected_dump_entries = all_entries if process_all else DumpRawData.objects.filter(
            project_number__in=selected_entries
        )

        for dump_entry in selected_dump_entries:
            project_number = dump_entry.project_number
            main_entry, created = Project.objects.get_or_create(project_number=project_number)

            # Ensure ForeignKey instances exist
            year_instance = Year.objects.get_or_create(year=dump_entry.year)[0] if dump_entry.year else None
            office_instance = Office.objects.get_or_create(office=dump_entry.office)[0] if dump_entry.office else None
            category_instance = Category.objects.get_or_create(category=dump_entry.category)[0] if dump_entry.category else None
            municipality_instance = Municipality.objects.get_or_create(municipality=dump_entry.municipality)[0] if dump_entry.municipality else None
            fund_instance = FundSource.objects.get_or_create(fund=dump_entry.fund)[0] if dump_entry.fund else None
            remarks_instance = Remark.objects.get_or_create(remark=dump_entry.remarks)[0] if dump_entry.remarks else None

            # Update Project fields
            for field in Project._meta.fields:
                if field.name in ["id", "updated_at", "sub_category"]:
                    continue

                old_value = getattr(main_entry, field.name, None)
                new_value = getattr(dump_entry, field.name, None)

                if field.name == "year":
                    new_value = year_instance
                elif field.name == "category":
                    new_value = category_instance
                elif field.name == "municipality":
                    new_value = municipality_instance
                elif field.name == "office":
                    new_value = office_instance
                elif field.name == "fund":
                    new_value = fund_instance

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=field.name,
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(main_entry, field.name, new_value)
            main_entry.save()

            # Update Contract fields
            contract_entry, _ = Contract.objects.get_or_create(project=main_entry)
            for field in Contract._meta.fields:
                if field.name in ["id", "project"]:
                    continue

                old_value = getattr(contract_entry, field.name, None)
                new_value = getattr(dump_entry, field.name, None)

                if field.name == "remarks":
                    new_value = remarks_instance

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=f"Contract: {field.name}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(contract_entry, field.name, new_value)
            contract_entry.save()

            # Update Timeline fields
            timeline_entry, _ = ProjectTimeline.objects.get_or_create(project=main_entry)
            for field in ProjectTimeline._meta.fields:
                if field.name in ["id", "project"]:
                    continue

                old_value = getattr(timeline_entry, field.name, None)
                new_value = getattr(dump_entry, field.name, None)

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=f"Timeline: {field.name}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(timeline_entry, field.name, new_value)
            timeline_entry.save()

        # ✅ Delete only selected DumpRawData entries
        DumpRawData.objects.filter(project_number__in=selected_entries).delete()

        messages.success(request, "Selected data merged successfully!")
        return redirect("update-history")

    return redirect("preview_merge_data")

#------------- Add New Project -------------#
ProjectTimelineFormSet = inlineformset_factory(Project, ProjectTimeline, form=ProjectTimelineForm, extra=1, can_delete=True)
ContractFormSet = inlineformset_factory(Project, Contract, form=ContractForm, extra=1, can_delete=True)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class CreateDataView(View):
    template_name = 'crud/add-infra.html'

    def get(self, request):
        form = ProjectForm()
        timeline_formset = ProjectTimelineFormSet(queryset=ProjectTimeline.objects.none())  # Ensure empty form
        contract_formset = ContractFormSet(queryset=Contract.objects.none())  # Ensure empty form

        return render(request, self.template_name, {
            'form': form,
            'timeline_formset': timeline_formset,
            'contract_formset': contract_formset,
            "page_title": "Add New Project"

        })

    def post(self, request):
        form = ProjectForm(request.POST)
        timeline_formset = ProjectTimelineFormSet(request.POST)
        contract_formset = ContractFormSet(request.POST)

        if form.is_valid() and timeline_formset.is_valid() and contract_formset.is_valid():
            new_entry = form.save(commit=False)  # Save without committing to modify ForeignKey fields
            
            # Handle Year (Check if exists, else create)
            if new_entry.year:
                year_value = int(new_entry.year.year)  # Assuming 'name' holds year values like '2024'
                existing_year, _ = Year.objects.get_or_create(year=year_value)
                new_entry.year = existing_year  # Assign the existing or new Year object

            # Assign correct ForeignKey IDs instead of objects
            category_id = new_entry.category.id if new_entry.category else None
            municipality_id = new_entry.municipality.id if new_entry.municipality else None
            fund_id = new_entry.fund.id if new_entry.fund else None
            office_id = new_entry.office.id if new_entry.office else None

            # Save the new project entry
            new_entry.save()

            # Save associated ProjectTimeline entries
            timeline_instances = timeline_formset.save(commit=False)
            for timeline in timeline_instances:
                timeline.project = new_entry  # Link to the project
                timeline.save()

            # Save associated Contract entries
            contract_instances = contract_formset.save(commit=False)
            for contract in contract_instances:
                contract.project = new_entry  # Link to the project
                contract.save()
            
            if timeline_instances:
                first_timeline = timeline_instances[0]  # Get the first contract instance
                cd = first_timeline.cd if hasattr(first_timeline, 'cd') else None
                ntp_date = first_timeline.ntp_date if hasattr(first_timeline, 'ntp_date') else None
                extension = first_timeline.extension if hasattr(first_timeline, 'extension') else None
                target_completion_date = first_timeline.target_completion_date if hasattr(first_timeline, 'target_completion_date') else None
                revised_completion_date = first_timeline.revised_completion_date if hasattr(first_timeline, 'revised_completion_date') else None
                total_cost_incured_to_date = first_timeline.total_cost_incurred_to_date if hasattr(first_timeline, 'total_cost_incured_to_date') else None                
                date_completed = first_timeline.date_completed if hasattr(first_timeline, 'date_completed') else None                
                reason = first_timeline.reason if hasattr(first_timeline, 'reason') else None
            
            # Extract remarks from the first contract instance (if any exist)
            remarks_id = None  # Default to None if no contracts exist
            if contract_instances:
                first_contract = contract_instances[0]  # Get the first contract instance
                remarks_id = first_contract.remarks.id if first_contract.remarks else None
                project_cost = first_contract.project_cost if hasattr(first_contract, 'project_cost') else None
                contract_cost = first_contract.contract_cost if hasattr(first_contract, 'contract_cost') else None
                quarter = first_contract.quarter if hasattr(first_contract, 'quarter') else None
                procurement = first_contract.procurement if hasattr(first_contract, 'procurement') else None                
                project_contractor = first_contract.project_contractor if hasattr(first_contract, 'project_contractor') else None                
                tin_number = first_contract.tin_number if hasattr(first_contract, 'tin_number') else None



            # Log the new project in history
            AddProjectHistory.objects.create(
                project_number=new_entry.project_number,
                project_name=new_entry.project_name,
                project_ID=new_entry.project_ID,
                category=category_id,
                project_description=new_entry.project_description,
                location=new_entry.location,
                municipality=municipality_id,
                office=office_id,
                year=new_entry.year.id,
                fund=fund_id,
                project_cost=project_cost,
                contract_cost=contract_cost,
                cd=cd,
                ntp_date=ntp_date,
                extension=extension,
                target_completion_date=target_completion_date,
                revised_completion_date=revised_completion_date,
                date_completed=date_completed,
                quarter=quarter,
                total_cost_incured_to_date=total_cost_incured_to_date,
                procurement=procurement,
                remarks=remarks_id,
                project_contractor=project_contractor,
                tin_number=tin_number,
                reason=reason,
                created_by=request.user
            )

            messages.success(request, "Project successfully added!")
            return redirect('add-history')

        return render(request, self.template_name, {
            'form': form,
            'timeline_formset': timeline_formset,
            'contract_formset': contract_formset
        })

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class AddHistoryView(View):
    """
    Displays all added history entries. Accessible by all users.
    """
    template_name = 'crud/history/add-history.html'

    def get(self, request):
        history = AddProjectHistory.objects.all().order_by('-created_at')

        # Define the list of columns and their display names for the preview
        column_list = [
            "project_number", "project_name", "project_ID", "category",
            "project_description", "location", "municipality", "office", "year",
            "fund", "project_cost", "contract_cost", "cd", "ntp_date", "extension",
            "target_completion_date", "revised_completion_date", "date_completed",
            "quarter", "total_cost_incured_to_date", "procurement", "remarks",
            "contractor", "tin_number", "reason"
        ]
        column_display_names = {
            "project_number": "No.",
            "project_name": "PGP Project Name",
            "project_ID": "Project ID",
            "category": "Project Category",
            "project_description": "Project Description",
            "location": "Location",
            "municipality": "Municipality",
            "office": "Implementing Office",
            "year": "Project Year",
            "fund": "Funding Source",
            "project_cost": "Project Cost",
            "contract_cost": "Contract Cost",
            "cd": "Contract Duration",
            "ntp_date": "NTP Date",
            "extension": "Extension",
            "target_completion_date": "Target Completion Date",
            "revised_completion_date": "Revised Completion Date",
            "date_completed": "Date Completed",
            "quarter": "Quarter",
            "total_cost_incured_to_date": "Total Cost Incurred to Date",
            "procurement": "Procurement Mode",
            "remarks": "General Remarks",
            "contractor": "Project Contractor",
            "tin_number": "TIN Number",
            "reason": "Reason"
        }

        return render(request, self.template_name, {
            'history': history, 
            "column_list": column_list, 
            "column_display_names": column_display_names,
            "page_title": "Added History"
        })

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class DeleteHistoryView(View):
    """
    Allows only Admins and Editors to delete history entries.
    """
    def post(self, request, pk):
        # Ensure only Admins and Editors can delete
        if not request.user.groups.filter(name__in=["Admin", "Editor"]).exists():
            messages.error(request, "You do not have permission to delete history entries.")
            return redirect('add-history')

        history_entry = get_object_or_404(AddProjectHistory, pk=pk)

        # Delete related project entry
        Project.objects.filter(project_number=history_entry.project_number).delete()

        # Delete related Contract and ProjectTimeline records
        Contract.objects.filter(project__project_number=history_entry.project_number).delete()
        ProjectTimeline.objects.filter(project__project_number=history_entry.project_number).delete()

        # Delete the history entry
        history_entry.delete()

        # Reset the auto-increment values
        self.reset_auto_increment("home_project", history_entry.project_number)
        self.reset_auto_increment("home_addprojecthistory", pk)

        messages.success(request, "History entry deleted successfully.")
        return redirect('add-history')

    def reset_auto_increment(self, table_name, start_value):
        """Resets the auto-increment value of a table."""
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {start_value};")

#------------- Profile -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor', 'Viewer']), name='dispatch')
class ProfileView(View):
    """View and Update User Profile"""

    def get(self, request):
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = PasswordUpdateForm()  # No need to pass 'user' here
        return render(request, "accounts/profile/profile.html", {
            "profile_form": profile_form,
            "password_form": password_form,
            "page_title": "Profile"
        })

    def post(self, request):
        profile_form = ProfileUpdateForm(request.POST, instance=request.user)
        password_form = PasswordUpdateForm(request.POST)

        if "update_profile" in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("profile")

        elif "change_password" in request.POST:
            if password_form.is_valid():
                new_password = password_form.cleaned_data["new_password"]

                # Apply Django's built-in password validators
                try:
                    validate_password(new_password, request.user)
                except ValidationError as e:
                    messages.error(request, "Password error: " + ", ".join(e.messages))
                    return redirect("profile")

                # Update password if validation passes
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps user logged in
                messages.success(request, "Password updated successfully!")
                return redirect("profile")

        messages.error(request, "Error updating profile. Please check the form.")
        return render(request, "accounts/profile/profile.html", {
            "profile_form": profile_form,
            "password_form": password_form,
            "page_title": "Profile"
        })

@method_decorator(allowed_user(roles=['Admin']), name='dispatch')
class AdminProfileView(View):
    """Admin Profile View - Manage Users, Roles, and Own Profile"""

    def get(self, request):
        if not request.user.is_superuser:
            messages.error(request, "Access Denied! Admins only.")
            return redirect("profile")

        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = PasswordUpdateForm()
        user_create_form = UserCreateForm()
        role_form = UserRoleForm()
        users = User.objects.all()
        groups = Group.objects.all()  # Fetch all groups (Admin, Editor, Viewer)

        return render(request, "accounts/profile/admin-profile.html", {
            "profile_form": profile_form,
            "password_form": password_form,
            "user_create_form": user_create_form,
            "role_form": role_form,
            "users": users,
            "groups": groups,
            "page_title": "AdminProfile"
        })

    def post(self, request):
        if not request.user.is_superuser:
            messages.error(request, "Access Denied! Admins only.")
            return redirect("profile")

        if "update_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("admin_profile")

        elif "change_password" in request.POST:
            password_form = PasswordUpdateForm(request.POST)
            if password_form.is_valid():
                new_password = password_form.cleaned_data["new_password"]
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep admin logged in
                messages.success(request, "Password updated successfully!")
                return redirect("admin_profile")

        elif "add_user" in request.POST:
            user_create_form = UserCreateForm(request.POST)
            if user_create_form.is_valid():
                user = user_create_form.save(commit=False)
                user.password = make_password(user_create_form.cleaned_data["password"])
                user.save()

                # Assign user to selected role
                role = request.POST.get("role")
                if role:
                    group = Group.objects.filter(name=role).first()
                    if group:
                        user.groups.add(group)

                messages.success(request, f"New user added successfully! Assigned role: {role}")
                return redirect("admin_profile")

        elif "assign_role" in request.POST:
            role_form = UserRoleForm(request.POST)
            if role_form.is_valid():
                user_id = role_form.cleaned_data["user"].id
                role = role_form.cleaned_data["role"]

                user = User.objects.get(id=user_id)
                group = Group.objects.filter(name=role).first()

                if group:
                    user.groups.clear()  # Remove existing roles
                    user.groups.add(group)
                    messages.success(request, f"{user.username} is now assigned as {role}.")
                else:
                    messages.error(request, "Invalid role selected.")

                return redirect("admin_profile")

        elif "delete_user" in request.POST:
            user_id = request.POST.get("user_id")
            try:
                user = User.objects.get(id=user_id)
                user.delete()
                messages.success(request, "User deleted successfully.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
            return redirect("admin_profile")

        elif "reset_password" in request.POST:
            user_id = request.POST.get("user_id")
            new_password = "defaultpassword123"  # Set a default password or generate one
            try:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password reset successfully. New password: {new_password}")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
            return redirect("admin_profile")

        messages.error(request, "Error processing the request.")
        return redirect("admin_profile")

#------------- Fund Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class FundTableView(ListView, FormView):    
    model = FundSource
    template_name = 'crud/instances/fund/fund.html'
    context_object_name = 'funds'
    paginate_by = 25
    form_class = FundSourceForm

    def get_queryset(self):
        queryset = FundSource.objects.all()
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(fund__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["search_query"] = self.request.GET.get("search", "")
        context['page_title'] = "Source Fund Table"
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            fund = form.save()
            messages.success(request, f"Fund '{fund.fund}' added successfully!")
            return redirect("fund_table")
        else:
            messages.error(request, "Error adding fund. Please check the input.")
            return self.get(request, *args, **kwargs)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class FundDeleteView(View):
    """Handles deleting a fund via AJAX"""
    def post(self, request, *args, **kwargs):
        try:
            fund_id = request.POST.get("fund_id")
            fund = FundSource.objects.get(id=fund_id)
            fund_name = fund.fund
            fund.delete()
            return JsonResponse({"success": True, "message": f"Fund '{fund_name}' deleted successfully!"})
        except FundSource.DoesNotExist:
            return JsonResponse({"success": False, "message": "Fund not found."})
        
#------------- Category Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class CategoryTableView(ListView, FormView):    
    model = Category
    template_name = 'crud/instances/category/category.html'
    context_object_name = 'category'
    paginate_by = 25
    form_class = CategoryForm

    def get_queryset(self):
        queryset = Category.objects.all()
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(category__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["search_query"] = self.request.GET.get("search", "")
        context['page_title'] = "Category Table"
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.category}' added successfully!")
            return redirect("category_table")
        else:
            messages.error(request, "Error adding category. Please check the input.")
            return self.get(request, *args, **kwargs)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class CategoryDeleteView(View):
    """Handles deleting a fund via AJAX"""
    def post(self, request, *args, **kwargs):
        try:
            category_id = request.POST.get("category_id")
            category = Category.objects.get(id=category_id)
            category_name = category.category
            category.delete()
            return JsonResponse({"success": True, "message": f"Category '{category_name}' deleted successfully!"})
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "message": "Category not found."})
        
#------------- Sub Category Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class SubCategoryTableView(ListView, FormView):    
    model = SubCategory
    template_name = 'crud/instances/subcategory/subcategory.html'
    context_object_name = 'subcategory'
    paginate_by = 25
    form_class = SubCategoryForm

    def get_queryset(self):
        queryset = SubCategory.objects.all()
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(sub_category__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["search_query"] = self.request.GET.get("search", "")
        context['page_title'] = "Sub Category Table"
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f"Sub Category '{subcategory.sub_category}' added successfully!")
            return redirect("subcategory_table")
        else:
            messages.error(request, "Error adding sub category. Please check the input.")
            return self.get(request, *args, **kwargs)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class SubCategoryDeleteView(View):
    """Handles deleting a subcategory via AJAX"""
    def post(self, request, *args, **kwargs):
        try:
            subcategory_id = request.POST.get("subcategory_id")
            subcategory = SubCategory.objects.get(id=subcategory_id)
            subcategory_name = subcategory.sub_category
            subcategory.delete()
            return JsonResponse({"success": True, "message": f"Sub Category '{subcategory_name}' deleted successfully!"})
        except SubCategory.DoesNotExist:
            return JsonResponse({"success": False, "message": "Sub Category not found."})

#------------- Fund Table -------------#
@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class OfficeTableView(ListView, FormView):    
    model = Office
    template_name = 'crud/instances/office/office.html'
    context_object_name = 'office'
    paginate_by = 25
    form_class = OfficeForm

    def get_queryset(self):
        queryset = Office.objects.all()
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(office__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["search_query"] = self.request.GET.get("search", "")
        context['page_title'] = "Office Table"
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            office = form.save()
            messages.success(request, f"Office '{office.office}' added successfully!")
            return redirect("office_table")
        else:
            messages.error(request, "Error adding office. Please check the input.")
            return self.get(request, *args, **kwargs)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class OfficeDeleteView(View):
    """Handles deleting a office via AJAX"""
    def post(self, request, *args, **kwargs):
        try:
            office_id = request.POST.get("office_id")
            office = Office.objects.get(id=office_id)
            office_name = office.office
            office.delete()
            return JsonResponse({"success": True, "message": f"Office '{office_name}' deleted successfully!"})
        except Office.DoesNotExist:
            return JsonResponse({"success": False, "message": "Office not found."})

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class YearTableView(ListView, FormView):    
    model = Year
    template_name = 'crud/instances/year/year.html'
    context_object_name = 'year'
    paginate_by = 25
    form_class = YearForm

    def get_queryset(self):
        queryset = Year.objects.all()
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(year__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["search_query"] = self.request.GET.get("search", "")
        context['page_title'] = "Year Table"
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            year = form.save()
            messages.success(request, f"Year '{year.year}' added successfully!")
            return redirect("year_table")
        else:
            messages.error(request, "Error adding year. Please check the input.")
            return self.get(request, *args, **kwargs)

@method_decorator(allowed_user(roles=['Admin', 'Editor']), name='dispatch')
class YearDeleteView(View):
    """Handles deleting a year via AJAX"""
    def post(self, request, *args, **kwargs):
        try:
            year_id = request.POST.get("year_id")
            year = Year.objects.get(id=year_id)
            year_x = year.year
            year.delete()
            return JsonResponse({"success": True, "message": f"Year '{year_x}' deleted successfully!"})
        except Year.DoesNotExist:
            return JsonResponse({"success": False, "message": "Year not found."})









