from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Purchase, QuickEntry, PurchaseCategory, Filter, Account, AccountUpdate, Recurring, Alert, Profile

from import_export.admin import ImportExportModelAdmin
from import_export import resources


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase

class QuickEntryResource(resources.ModelResource):
    class Meta:
        model = QuickEntry

class PurchaseCategoryResource(resources.ModelResource):
    class Meta:
        model = PurchaseCategory

class FilterResource(resources.ModelResource):
    class Meta:
        model = Filter

class RecurringResource(resources.ModelResource):
    class Meta:
        model = Recurring

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account

class AccountUpdateResource(resources.ModelResource):
    class Meta:
        model = AccountUpdate

class AlertResource(resources.ModelResource):
    class Meta:
        model = Alert


@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('id', 'user', 'date', 'time', 'category', 'item', 'amount', 'category_2', 'amount_2', 'description', 'currency', 'exchange_rate')
    list_filter = ['user', 'date', 'category', 'item', 'currency']

@admin.register(QuickEntry)
class QuickEntryAdmin(ImportExportModelAdmin):
    resource_class = QuickEntryResource
    list_display = ('user', 'category', 'item', 'amount', 'category_2', 'amount_2', 'description')
    list_filter = ['user', 'category', 'item']

@admin.register(PurchaseCategory)
class PurchaseCategoryAdmin(ImportExportModelAdmin):
    resource_class = PurchaseCategoryResource
    list_display = ('id', 'category', 'threshold', 'threshold_rolling_days', 'category_created_datetime')
    readonly_fields = ('category_created_datetime',)

@admin.register(Filter)
class FilterAdmin(ImportExportModelAdmin):
    resource_class = FilterResource
    list_display = ('id', 'page', 'category_filter_1', 'category_filter_2', 'category_filter_3', 'start_date_filter', 'end_date_filter', 'last_updated')
    readonly_fields = ('last_updated',)

@admin.register(Recurring)
class RecurringAdmin(ImportExportModelAdmin):
    resource_class = RecurringResource
    list_display = ('name', 'type', 'account', 'active', 'amount')

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('id', 'account', 'active', 'credit', 'currency', 'account_created_datetime')
    readonly_fields = ('account_created_datetime',)

@admin.register(AccountUpdate)
class AccountUpdateAdmin(ImportExportModelAdmin):
    resource_class = AccountUpdateResource
    list_display = ('account', 'value', 'exchange_rate', 'timestamp')
    list_filter = ['account']
    readonly_fields = ('timestamp',)

@admin.register(Alert)
class AlertAdmin(ImportExportModelAdmin):
    resource_class = AlertResource
    list_display = ('type', 'percent', 'date_sent')
    readonly_fields = ('date_sent',)
