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

from django.views import View
from django.views.generic.list import ListView

#------------- Models -------------#
# Main table
from .models import Project, Contract, ProjectTimeline
# Foreign table
from .models import Category, SubCategory, Municipality, Year, Office, Contractor, FundSource, Remark
# History Table
from .models import UpdateHistory

#------------- Forms -------------#
# Auth Form
from apps.authentication.forms import UpdateForm, ProjectTimelineForm, ContractForm

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
            queryset = queryset.filter(fund_source__fund=fund)
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
            total_cost=F("timeline__total_cost_Incurred_to_date"),
            reason=F("timeline__reason"),

            # Contract 
            project_cost=F("contract__project_cost"),
            contract_cost=F("contract__contract_cost"),
            procurement=F("contract__procurement"),
            quarter=F("contract__quarter"),
            remarks=F("contract__remarks__remark"),
            contractor=F("contract__contractor__contractor"),
            tin_number=F("contract__contractor__tin_number"),
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
ProjectTimelineFormSet = inlineformset_factory(Project, ProjectTimeline, form=ProjectTimelineForm, extra=1, can_delete=True)
ContractFormSet = inlineformset_factory(Project, Contract, form=ContractForm, extra=1, can_delete=True)

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

        # Fetch the original values before updating
        original_project = Project.objects.get(pk=pk)
        
        form = UpdateForm(request.POST, instance=project)
        timeline_formset = ProjectTimelineFormSet(request.POST, instance=project)
        contract_formset = ContractFormSet(request.POST, instance=project)

        if form.is_valid() and timeline_formset.is_valid() and contract_formset.is_valid():
            # Track changes in the Project model
            for field in form.changed_data:
                old_value = getattr(original_project, field) or ""  # Handle None values
                new_value = form.cleaned_data[field] or ""

                print(f"Updating '{field}': '{old_value}' -> '{new_value}'")  # Debugging changed fields

                UpdateHistory.objects.create(
                    project=project,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                    updated_by=request.user
                )

            # Save main Project form and related formsets
            form.save()
            timeline_formset.save()
            contract_formset.save()

            return redirect('update_data')

        return render(request, self.template_name, {
            'form': form,
            'project': project,
            'timeline_formset': timeline_formset,
            'contract_formset': contract_formset
        })
    