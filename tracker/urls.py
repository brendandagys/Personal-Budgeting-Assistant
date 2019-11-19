from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    # Regex is for date and for category
    re_path(r'^transactions/?([\w_]*)/?([\w_]*)$', views.PurchaseListView.as_view(), name='transactions'),

    # path('transactions/', views.PurchaseListView.as_view(), name='purchases'),
]
