from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from . import views


urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('activity/', login_required(views.PurchaseListView.as_view()), name='activity'),
    path('activity/get_accounts_sum/', views.get_accounts_sum),
    path('activity/get_purchases/', views.get_json_queryset),
    path('activity/filters/', views.filter_manager),
    path('activity/account_update/', views.account_update),
    path('activity/reset_credit_card/', views.reset_credit_card),
    path('preferences/', views.preferences, name='preferences'),
    path('charts/', views.get_chart_data),
    path('mode/', views.mode_manager),
]
