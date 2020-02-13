from django.contrib import admin

from .models import Purchase, Filter, Bill, Alert

from import_export.admin import ImportExportModelAdmin
from import_export import resources

class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase

@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('date', 'time', 'category', 'category_2', 'item', 'amount')
    list_filter = ['date', 'category', 'category_2', 'item']

@admin.register(Filter)
class FiltersAdmin(ImportExportModelAdmin):
    resource_class = Filter

@admin.register(Bill)
class BillAdmin(ImportExportModelAdmin):
    resource_class = Bill

@admin.register(Alert)
class AlertAdmin(ImportExportModelAdmin):
    resource_class = Alert
