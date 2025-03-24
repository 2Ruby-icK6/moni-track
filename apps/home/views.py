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

from django.views import View
from django.views.generic.list import ListView

import os
import re
import json

from .utils import utils

#------------- Models -------------#
# Main table
from .models import Project, Contract, ProjectTimeline, DumpRawData
# Foreign table
from .models import Category, SubCategory, Municipality, Year, Office, FundSource, Remark
# History Table
from .models import UpdateHistory

#------------- Forms -------------#
# Auth Form
from apps.authentication.forms import UpdateForm, ProjectForm, ProjectTimelineForm, ContractForm, UploadFileForm

#------------- Login -------------#
@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('accounts/error/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('accounts/error/page-500.html')
        return HttpResponse(html_template.render(context, request))

#------------- Projects Dashboard -------------#
class ProjectListView(ListView):
    model = Project
    template_name = 'home/dashboard.html'
    context_object_name = 'projects'
    paginate_by = 5

    def get_queryset(self):
        queryset = Project.objects.all()

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['category'] = Category.objects.values_list('category', flat=True).distinct().order_by('category')
        context['fund'] = FundSource.objects.values_list('fund', flat=True).distinct().order_by('fund')
        context['municipality'] = Municipality.objects.values_list('municipality', flat=True).distinct().order_by('municipality')
        context['office'] = Office.objects.values_list('office', flat=True).distinct().order_by('office')
        context['sub_category'] = SubCategory.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        context['year'] = Year.objects.values_list('year', flat=True).distinct().order_by('year')

        return context

#------------- Projects Table -------------#
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

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pass available filter options to the template
        context['category'] = Category.objects.values_list('category', flat=True).distinct().order_by('category')
        context['fund'] = FundSource.objects.values_list('fund', flat=True).distinct().order_by('fund')
        context['municipality'] = Municipality.objects.values_list('municipality', flat=True).distinct().order_by('municipality')
        context['office'] = Office.objects.values_list('office', flat=True).distinct().order_by('office')
        context['sub_category'] = SubCategory.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        context['year'] = Year.objects.values_list('year', flat=True).distinct().order_by('year')
        context['remark'] = Remark.objects.values_list('remark', flat=True).distinct().order_by('remark')

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
class ProjectFlexTableView(ListView):
    model = Project
    template_name = "home/flex-tables.html"
    context_object_name = "projects"
    paginate_by = 10

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
    
#------------- Download Table Preview -------------#
class DonwloadTablePreview(ListView):
    model = Project
    template_name = 'file/download-file.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.select_related(
            "timeline",   # Fetch related ProjectTimeline
            "contract"    # Fetch related Contract
        ).all()

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['category'] = Category.objects.values_list('category', flat=True).distinct().order_by('category')
        context['fund'] = FundSource.objects.values_list('fund', flat=True).distinct().order_by('fund')
        context['municipality'] = Municipality.objects.values_list('municipality', flat=True).distinct().order_by('municipality')
        context['office'] = Office.objects.values_list('office', flat=True).distinct().order_by('office')
        context['sub_category'] = SubCategory.objects.values_list('sub_category', flat=True).distinct().order_by('sub_category')
        context['year'] = Year.objects.values_list('year', flat=True).distinct().order_by('year')
        context['remark'] = Remark.objects.values_list('remark', flat=True).distinct().order_by('remark')

        return context

#------------- Udpate Project -------------#
# Create inline formsets for ProjectTimeline and Contract
ProjectTimelineFormSet = inlineformset_factory(Project, ProjectTimeline, form=ProjectTimelineForm, extra=0, can_delete=True)
ContractFormSet = inlineformset_factory(Project, Contract, form=ContractForm, extra=0, can_delete=True)

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
            'contract_formset': contract_formset
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
            'contract_formset': contract_formset
        })

#------------- Udpate History Project -------------#
class UpdateHistoryView(ListView):
    """
    Displays update history for the logged-in user and provides actions
    to revert (undo) or accept changes.
    """
    model = UpdateHistory
    template_name = "crud/history/update-history.html"
    context_object_name = "history_entries"
    ordering = ["-updated_at"]

    def get_queryset(self):
        return UpdateHistory.objects.filter(updated_by=self.request.user)

class UpdateHistoryActionView(View):
    """
    Handles user actions: revert (undo) or accept changes.
    """

    def post(self, request, history_id, action):
        history_entry = get_object_or_404(UpdateHistory, id=history_id, updated_by=request.user)
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
        
        elif action == "accept":
            history_entry.delete()
            messages.success(request, f"Accepted change for {field_name}.")

        return redirect("update-history")

#------------- Upload File -------------#
class ImportAndPreviewView(View):
    template_name = "crud/file/import-file.html"

    def get(self, request):
        """Handles GET requests - renders the form and paginated data preview."""
        form = UploadFileForm()
        context = self.get_context_data(request, form)
        return render(request, self.template_name, context)

    def post(self, request):
        """Handles POST requests - processes file upload and data import."""
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES["file"]
            if not file.name.endswith((".xlsx", ".xls")):
                messages.error(request, "Invalid file format. Please upload an Excel file.")
                return redirect("import_file")

            try:
                temp_json_path, data = self.process_file(file)

                quarter_column = self.detect_quarter_column(data)
                if not quarter_column:
                    raise ValueError("Error: 'Quarter' column not found in the dataset.")

                # Clear previous imports before adding new data
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
        """Saves file temporarily, converts it to JSON, and returns data."""
        temp_excel_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(temp_excel_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        temp_json_path = os.path.splitext(temp_excel_path)[0] + ".json"
        utils.excel_to_json(temp_excel_path, temp_json_path)

        with open(temp_json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        os.remove(temp_excel_path)  # Remove Excel file after conversion
        return temp_json_path, data

    def detect_quarter_column(self, data):
        """Finds the column name matching 'AS OF [MONTH] [YEAR]' format."""
        for key in data[0].keys():
            if re.search(r"AS OF [A-Z]+ \d{4}", key, re.IGNORECASE):
                return key
        return None

    def save_data(self, data, quarter_column):
        """Saves the imported data into the database."""
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
            "column_display_names": column_display_names
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

    # Foreign key mappings
    category_mapping = {c.category: c for c in Category.objects.all()}
    municipality_mapping = {m.municipality: m for m in Municipality.objects.all()}
    year_mapping = {y.year: y for y in Year.objects.all()}
    fund_mapping = {f.fund: f for f in FundSource.objects.all()}
    remark_mapping = {r.remark: r for r in Remark.objects.all()}

    foreign_key_fields = {
        "category": category_mapping,
        "municipality": municipality_mapping,
        "fund": fund_mapping,
        "year": year_mapping,
    }

    for dump_entry in dump_data:
        try:
            main_entry = Project.objects.get(project_number=dump_entry.project_number)
        except Project.DoesNotExist:
            continue

        entry_changes = {
            "project_number": dump_entry.project_number,
            "project_name": dump_entry.project_name,
            "fields": [],
            "exists": True,
        }

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

    return render(request, "crud/file/merge-preview.html", {"changes": changes})

def compare_project_fields(main_entry, dump_entry, foreign_key_fields):
    """ Compare only fields that belong to the Project model, excluding 'sub_category' """
    changes = []
    project_fields = [field.name for field in Project._meta.fields]
    ignored_fields = ["id", "updated_at", "sub_category"]

    for field_name in project_fields:
        if field_name in ignored_fields or not hasattr(dump_entry, field_name):
            continue

        old_value = getattr(main_entry, field_name, None)
        new_value = getattr(dump_entry, field_name, None)

        if field_name in foreign_key_fields:
            mapping = foreign_key_fields[field_name]
            old_value = str(old_value) if old_value else "-"
            new_value = str(mapping.get(new_value, "-"))

        old_value = str(old_value) if old_value is not None else "-"
        new_value = str(new_value) if new_value is not None else "-"

        if old_value != new_value:
            changes.append({
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value
            })

    return changes

def compare_contract_fields(contract_entry, dump_entry):
    """ Compare only fields that belong to the Contract model """
    changes = []
    contract_fields = [field.name for field in Contract._meta.fields]

    for field_name in contract_fields:
        if field_name in ["id", "project"] or not hasattr(dump_entry, field_name):
            continue

        old_value = getattr(contract_entry, field_name, None)
        new_value = getattr(dump_entry, field_name, None)

        if field_name == "remarks":
            old_value = old_value.remark if old_value else "-"
            new_value = str(new_value) if new_value else "-"

        old_value = str(old_value) if old_value is not None else "-"
        new_value = str(new_value) if new_value is not None else "-"

        if old_value != new_value:
            changes.append({
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value
            })

    return changes

def compare_timeline_fields(timeline_entry, dump_entry):
    """ Compare only fields that belong to the ProjectTimeline model """
    changes = []
    timeline_fields = [field.name for field in ProjectTimeline._meta.fields]

    for field_name in timeline_fields:
        if field_name in ["id", "project"] or not hasattr(dump_entry, field_name):
            continue

        old_value = getattr(timeline_entry, field_name, None)
        new_value = getattr(dump_entry, field_name, None)

        old_value = str(old_value) if old_value is not None else "-"
        new_value = str(new_value) if new_value is not None else "-"

        if old_value != new_value:
            changes.append({
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value
            })

    return changes

def merge_selected_data(request):
    if request.method == "POST":
        selected_entries = request.POST.getlist("selected_entries")

        if not selected_entries:
            messages.warning(request, "No entries selected for merging.")
            return redirect("preview_merge_data")

        all_entries = DumpRawData.objects.all()
        process_all = "ALL" in selected_entries  # Check if 'ALL' is selected

        for dump_entry in (all_entries if process_all else [DumpRawData.objects.get(project_number=entry.split("_")[0]) for entry in selected_entries]):
            project_number = dump_entry.project_number
            main_entry, created = Project.objects.get_or_create(project_number=project_number)

            # Ensure ForeignKey instances exist
            year_instance = Year.objects.get_or_create(year=dump_entry.year)[0] if dump_entry.year else None
            office_instance = Office.objects.get_or_create(office=dump_entry.office)[0] if dump_entry.office else None
            category_instance = Category.objects.get_or_create(category=dump_entry.category)[0] if dump_entry.category else None
            municipality_instance = Municipality.objects.get_or_create(municipality=dump_entry.municipality)[0] if dump_entry.municipality else None
            fund_instance = FundSource.objects.get_or_create(fund=dump_entry.fund)[0] if dump_entry.fund else None
            remarks_instance = Remark.objects.get_or_create(remark=dump_entry.remarks)[0] if dump_entry.remarks else None

            for field_name in Project._meta.fields:
                if field_name.name in ["id", "updated_at", "sub_category"]:
                    continue

                old_value = getattr(main_entry, field_name.name, None)
                new_value = getattr(dump_entry, field_name.name, None)

                if field_name.name == "year":
                    new_value = year_instance
                elif field_name.name == "category":
                    new_value = category_instance
                elif field_name.name == "municipality":
                    new_value = municipality_instance
                elif field_name.name == "office":
                    new_value = office_instance
                elif field_name.name == "fund":
                    new_value = fund_instance

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=field_name.name,
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(main_entry, field_name.name, new_value)
            main_entry.save()

            contract_entry, _ = Contract.objects.get_or_create(project=main_entry)
            for field_name in Contract._meta.fields:
                if field_name.name in ["id", "project"]:
                    continue

                old_value = getattr(contract_entry, field_name.name, None)
                new_value = getattr(dump_entry, field_name.name, None)

                if field_name.name == "remarks":
                    new_value = remarks_instance

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=f"Contract: {field_name.name}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(contract_entry, field_name.name, new_value)
            contract_entry.save()

            timeline_entry, _ = ProjectTimeline.objects.get_or_create(project=main_entry)
            for field_name in ProjectTimeline._meta.fields:
                if field_name.name in ["id", "project"]:
                    continue

                old_value = getattr(timeline_entry, field_name.name, None)
                new_value = getattr(dump_entry, field_name.name, None)

                if old_value != new_value:
                    UpdateHistory.objects.create(
                        project=main_entry,
                        field_name=f"Timeline: {field_name.name}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=request.user
                    )
                    setattr(timeline_entry, field_name.name, new_value)
            timeline_entry.save()

        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE home_dumprawdata;")

        messages.success(request, "Selected data merged successfully!")
        return redirect("update-history")

    return redirect("preview_merge_data")


