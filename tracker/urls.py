from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('transactions/', views.PurchaseListView.as_view(), name='transactions'),
    path('transactions/updatefilter/', views.filter_manager),
]
