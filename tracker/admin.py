from django.contrib import admin

from .models import Purchase, PurchaseCategory, Filter, Account, AccountUpdate, Bill, Alert, Mode

from import_export.admin import ImportExportModelAdmin
from import_export import resources

class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase

@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('date', 'time', 'category', 'category_2', 'item', 'amount')
    list_filter = ['date', 'category', 'item']

@admin.register(PurchaseCategory)
class PurchaseCategoryAdmin(ImportExportModelAdmin):
    resource_class = PurchaseCategory
    list_display = ('category',)
    readonly_fields = ('category_created_datetime',)

@admin.register(Filter)
class FiltersAdmin(ImportExportModelAdmin):
    resource_class = Filter
    list_display = ('category_filter_1', 'category_filter_2', 'category_filter_3', 'start_date_filter', 'end_date_filter', 'last_updated')
    readonly_fields = ('last_updated',)

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = Account

@admin.register(AccountUpdate)
class AccountUpdateAdmin(ImportExportModelAdmin):
    resource_class = AccountUpdate

@admin.register(Bill)
class BillAdmin(ImportExportModelAdmin):
    resource_class = Bill

@admin.register(Alert)
class AlertAdmin(ImportExportModelAdmin):
    resource_class = Alert

@admin.register(Mode)
class ModeAdmin(ImportExportModelAdmin):
    resource_class = Mode
