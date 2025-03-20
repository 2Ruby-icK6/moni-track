# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

#------------- Views -------------#
from apps.home.views import ProjectListView, ProjectTableView, ProjectFlexTableView
from apps.home.views import DonwloadTablePreview

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    path('dashboard/', ProjectListView.as_view(), name='dashboard'),
    path('project-table/', ProjectTableView.as_view(), name='project_table'),
    path('project-flextable/', ProjectFlexTableView.as_view(), name='project_flextable'),

    path('download/', DonwloadTablePreview.as_view(), name='download_file'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),


]
