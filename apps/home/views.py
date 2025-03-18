# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from django.views import View
from django.views.generic.list import ListView

#------------- Models -------------#
# Main table
from .models import Project, Contract, ProjectTimeline
# Foreign table
from .models import Category, SubCategory, Municipality, Year, Office, Contractor, FundSource, Remark

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
    context_object_name = 'project_data'
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