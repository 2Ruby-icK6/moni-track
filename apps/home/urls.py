# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

#------------- Views -------------#
from apps.home.views import ProjectListView, ProjectTableView, ProjectFlexTableView
from apps.home.views import DonwloadTablePreview, export_data, UpdateDataView, UpdateHistoryView, UpdateHistoryActionView
from apps.home.views import ImportAndPreviewView, discard_data, preview_merge_data, merge_selected_data
from apps.home.views import CreateDataView, AddHistoryView, DeleteHistoryView, FundTableView, FundDeleteView

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    path('dashboard/', ProjectListView.as_view(), name='dashboard'),
    path('project-table/', ProjectTableView.as_view(), name='project_table'),
    path('project-flextable/', ProjectFlexTableView.as_view(), name='project_flextable'),

    path('download/', DonwloadTablePreview.as_view(), name='download_file'),
    path("export/", export_data, name="export_data"),

    path('update/', UpdateDataView.as_view(), name='update_data'),  
    path('update/<int:pk>/', UpdateDataView.as_view(), name='update_data_with_pk'),

    path("history/", UpdateHistoryView.as_view(), name="update-history"),
    path("history/action/<int:history_id>/<str:action>/", UpdateHistoryActionView.as_view(), name="update-history-action"),

    path('import/', ImportAndPreviewView.as_view(), name='import_file'),
    path("discard/", discard_data, name="discard_data"),

    path("merge-preview/", preview_merge_data, name="merge_preview"),
    path("merge-selected/", merge_selected_data, name="merge_selected_data"),

    path('create/', CreateDataView.as_view(), name='add_project'),
    path('create-history/', AddHistoryView.as_view(), name='add-history'),
    path('history/delete/<int:pk>/', DeleteHistoryView.as_view(), name='delete_history'),

    path("funds/", FundTableView.as_view(), name="fund_table"),
    path("funds/delete/", FundDeleteView.as_view(), name="fund_delete"),


    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),


]
