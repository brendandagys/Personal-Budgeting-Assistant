from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('transactions/', login_required(views.PurchaseListView.as_view()), name='transactions'),
    path('transactions/filter/', views.filter_manager),
    path('charts/', views.get_chart_data),
]
