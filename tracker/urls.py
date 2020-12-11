from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('transactions/', login_required(views.PurchaseListView.as_view()), name='transactions'),
    path('transactions/get_purchases/', views.get_json_queryset),
    path('transactions/filters/', views.filter_manager),
    path('transactions/account_update/', views.account_update),
    path('charts/', views.get_chart_data),
    path('mode/', views.mode_manager),
]
