from django.contrib import admin

from .models import Purchase, PurchaseCategory, Filter, Account, AccountUpdate, Bill, Alert, Mode

from import_export.admin import ImportExportModelAdmin
from import_export import resources

class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase

class BillResource(resources.ModelResource):
    class Meta:
        model = Bill

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account

class AccountUpdateResource(resources.ModelResource):
    class Meta:
        model = AccountUpdate

class PurchaseCategoryResource(resources.ModelResource):
    class Meta:
        model = PurchaseCategory

@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('date', 'time', 'category', 'category_2', 'item', 'amount', 'amount_2', 'description')
    list_filter = ['date', 'category', 'item']

@admin.register(PurchaseCategory)
class PurchaseCategoryAdmin(ImportExportModelAdmin):
    resource_class = PurchaseCategoryResource
    list_display = ('id', 'category', 'category_created_datetime')
    readonly_fields = ('category_created_datetime',)

@admin.register(Filter)
class FiltersAdmin(ImportExportModelAdmin):
    resource_class = Filter
    list_display = ('category_filter_1', 'category_filter_2', 'category_filter_3', 'start_date_filter', 'end_date_filter', 'last_updated')
    readonly_fields = ('last_updated',)

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('account', 'active', 'credit', 'currency', 'account_created_datetime')
    readonly_fields = ('account_created_datetime',)

@admin.register(AccountUpdate)
class AccountUpdateAdmin(ImportExportModelAdmin):
    resource_class = AccountUpdateResource
    list_display = ('account', 'value', 'exchange_rate', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(Bill)
class BillAdmin(ImportExportModelAdmin):
    resource_class = BillResource
    list_display = ('bill', 'active', 'amount', 'frequency')

@admin.register(Alert)
class AlertAdmin(ImportExportModelAdmin):
    resource_class = Alert
    list_display = ('type', 'percent', 'date_sent')
    readonly_fields = ('date_sent',)

@admin.register(Mode)
class ModeAdmin(ImportExportModelAdmin):
    resource_class = Mode
    list_display = ('mode',)
