from django.db import models
import django_filters

import datetime
from django.utils import timezone

def current_date():
    return datetime.date.today()

def current_time():
    return str(timezone.now().time())[0:5]

def current_datetime():
    return timezone.now()


class PurchaseCategory(models.Model):
    category = models.CharField(primary_key=True, max_length=30, verbose_name='Category')
    category_created_datetime = models.DateTimeField(default=current_datetime, verbose_name='Category Created DateTime') # Any field with the auto_now attribute set will also inherit editable=False and won't show in admin panel

    class Meta:
        verbose_name_plural = 'Purchase Categories'
        verbose_name = 'Purchase Category'

    def __str__(self):
        return ', '.join([self.category])


# Ensure that these exist, otherwise we'll get an IntegrityError for the existing Purchases
# for category in ['', 'Coffee', 'Food/Drinks', 'Groceries', 'Restaurants', 'Bills', 'Gas', 'Household Supplies', 'Services', 'Dates', 'Gifts', 'Tickets', 'Electronics', 'Appliances', 'Clothes', 'Alcohol', 'Vacation', 'Fees']:
#     temp = PurchaseCategory.objects.get_or_create(category=category)


class Purchase(models.Model):
    # null and blank arguments are False by default
    # null doesn't allow null in the database, blank is not database-related; it prevents '' in forms
    date = models.DateField(verbose_name='Date', default=current_date)
    time = models.CharField(max_length=20, verbose_name='Time (24 hr.)', default=current_time)
    item = models.CharField(max_length=100, verbose_name='Item(s)')
    # category = models.CharField(blank=True, null=True, max_length=50, verbose_name='Category')
    category = models.ForeignKey(PurchaseCategory, null=True, on_delete=models.SET_NULL, verbose_name='Category', related_name='category_1') # blank=False by default...
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')
    # category_2 = models.ForeignKey(PurchaseCategory, null=True, on_delete=models.SET_NULL, verbose_name='Category 2', related_name='category_2')
    amount_2 = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2, verbose_name='Amount 2')
    description = models.TextField(blank=True, verbose_name='Details')

    class Meta:
        verbose_name_plural = 'Purchases'
        verbose_name = 'Purchase'

    def __str__(self):
        return ', '.join([str(self.date), self.time, str(self.category.category), self.item, str(self.amount)])


class Filter(models.Model):
    last_update_date = models.DateField(verbose_name='Last Update Date', default=current_date)
    last_update_time = models.CharField(max_length=30, verbose_name = 'Time (24 hr.)', default=current_time)
    category_filter = models.CharField(max_length=20, verbose_name = 'Category Filter')
    time_filter = models.CharField(max_length=20, verbose_name = 'Time Filter')
    deactivate_category = models.CharField(max_length=5, verbose_name = 'Deactivate Category', default='No')
    deactivate_time = models.CharField(max_length=5, verbose_name = 'Deactivate Time', default='No')

    class Meta:
        verbose_name_plural = 'Filters'
        verbose_name = 'Filter'

    def __str__(self):
        return ', '.join([str(self.last_update_date), self.last_update_time])


class Account(models.Model):
    account = models.CharField(primary_key=True, max_length=40, verbose_name='Account')
    active = models.BooleanField(default=True, verbose_name='Active')
    account_created_datetime = models.DateTimeField(default=current_datetime, verbose_name='Account Created DateTime')

    class Meta:
        verbose_name_plural = 'Accounts'
        verbose_name = 'Account'

    def __str__(self):
        return ', '.join([self.account, str(self.active), str(self.account_created_datetime)])


class AccountUpdate(models.Model):
    account = models.ForeignKey(PurchaseCategory, null=True, on_delete=models.SET_NULL, verbose_name='Account')
    value = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Value')
    timestamp = models.DateTimeField(default=current_datetime, verbose_name='Account Timestamp')

    class Meta:
        verbose_name_plural = 'Account Updates'
        verbose_name = 'Account Update'

    def __str__(self):
        return ', '.join([str(self.account), str(self.value), str(self.timestamp)])


class Bill(models.Model):
    bill = models.CharField(primary_key=True, max_length=40, verbose_name = 'Bill')
    active = models.BooleanField(default=True, verbose_name='Active')
    frequency = models.CharField(max_length=100, verbose_name='Frequency')

    class Meta:
        verbose_name_plural = 'Bills'
        verbose_name = 'Bill'

    def __str__(self):
        return ', '.join([self.bill, str(self.active), self.frequency])


class Alert(models.Model):
    type = models.CharField(max_length=20, verbose_name = 'Type')
    percent = models.IntegerField(verbose_name = 'Percent')
    date_sent = models.DateField(verbose_name='Date Sent')

    class Meta:
        verbose_name_plural = 'Alerts'
        verbose_name = 'Alert'

    def __str__(self):
        return ', '.join([self.type, str(self.percent), str(self.date_sent)])


class Mode(models.Model):
    mode = models.CharField(max_length=10, verbose_name = 'Mode')

    class Meta:
        verbose_name_plural = 'Modes'
        verbose_name = 'Mode'

    def __str__(self):
        return self.mode
