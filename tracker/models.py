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

CURRENCIES = [
    ('CAD', 'CAD'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
]

class PurchaseCategory(models.Model):
    category = models.CharField(max_length=30, verbose_name='Category')
    threshold = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2, verbose_name='Threshold')
    threshold_rolling_days = models.PositiveIntegerField(default=30, verbose_name='Threshold Rolling Days')
    category_created_datetime = models.DateTimeField(auto_now_add=True, verbose_name='Category Created DateTime') # Any field with the auto_now attribute set will also inherit editable=False and won't show in admin panel

    class Meta:
        verbose_name_plural = 'Purchase Categories'
        verbose_name = 'Purchase Category'
        ordering = ['id']

    def __str__(self):
        return ', '.join([self.category, str(self.threshold), str(self.threshold_rolling_days) + ' days'])


class Purchase(models.Model):
    # null and blank arguments are False by default
    # null doesn't allow null in the database, blank is not database-related; it prevents '' in forms
    date = models.DateField(verbose_name='Date', default=current_date)
    time = models.CharField(blank=True, default=current_time, max_length=5, verbose_name='Time (24 hr.)')
    item = models.CharField(max_length=100, verbose_name='Item(s)')
    category = models.ForeignKey(PurchaseCategory, null=True, on_delete=models.SET_NULL, verbose_name='Category', related_name='category_1') # blank=False by default...
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')
    category_2 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category 2', related_name='category_2')
    amount_2 = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2, verbose_name='Amount 2')
    description = models.TextField(blank=True, verbose_name='Details')
    currency = models.CharField(choices=CURRENCIES, default='CAD', max_length=10, verbose_name='Currency')
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Exchange Rate to CAD') # Default 1 unnecessary as we always run get_exchange_rate()

    class Meta:
        verbose_name_plural = 'Purchases'
        verbose_name = 'Purchase'

    def __str__(self):
        return ', '.join([str(self.date), self.time, str(self.category.category), str(self.category.category_2), self.item, str(self.amount)])


class Filter(models.Model):
    category_filter_1 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 1', related_name='category_filter_1')
    category_filter_2 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 2', related_name='category_filter_2')
    category_filter_3 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 3', related_name='category_filter_3')
    category_filter_4 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 4', related_name='category_filter_4')
    category_filter_5 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 5', related_name='category_filter_5')
    category_filter_6 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 6', related_name='category_filter_6')
    category_filter_7 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 7', related_name='category_filter_7')
    category_filter_8 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 8', related_name='category_filter_8')
    category_filter_9 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 9', related_name='category_filter_9')
    category_filter_10 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 10', related_name='category_filter_10')
    start_date_filter = models.DateField(blank=True, null=True, verbose_name = 'Start Date')
    end_date_filter = models.DateField(blank=True, null=True, verbose_name = 'End Date')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Filter Last Updated')

    class Meta:
        verbose_name_plural = 'Filters'
        verbose_name = 'Filter'

    def __str__(self):
        return ', '.join([str(self.category_filter_1), str(self.start_date_filter), str(self.end_date_filter)])


class Account(models.Model):
    account = models.CharField(max_length=40, verbose_name='Account')
    credit = models.BooleanField(default=False, verbose_name='Credit')
    currency = models.CharField(choices=CURRENCIES, default='CAD', max_length=10, verbose_name='Currency')
    active = models.BooleanField(default=True, verbose_name='Active')
    account_created_datetime = models.DateTimeField(auto_now_add=True, verbose_name='Account Created DateTime')

    class Meta:
        verbose_name_plural = 'Accounts'
        verbose_name = 'Account'
        ordering = ['account']

    def __str__(self):
        return ', '.join([self.account, str(self.credit), str(self.active), str(self.account_created_datetime)])


class AccountUpdate(models.Model):
    account = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL, verbose_name='Account')
    value = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Value')
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Exchange Rate to CAD') # Default 1 unnecessary as we always run get_exchange_rate()
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Account Timestamp')

    class Meta:
        verbose_name_plural = 'Account Updates'
        verbose_name = 'Account Update'
        ordering = ['-timestamp']

    def __str__(self):
        return ', '.join([str(self.account), str(self.value), str(self.timestamp)])


class Bill(models.Model):
    bill = models.CharField(max_length=40, verbose_name='Bill')
    active = models.BooleanField(default=True, verbose_name='Active')
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')
    frequency = models.CharField(max_length=100, verbose_name='Frequency')

    class Meta:
        verbose_name_plural = 'Bills'
        verbose_name = 'Bill'
        ordering = ['-amount']

    def __str__(self):
        return ', '.join([self.bill, str(self.active), self.frequency])


class Alert(models.Model):
    type = models.CharField(max_length=20, verbose_name = 'Type')
    percent = models.PositiveIntegerField(verbose_name = 'Percent')
    date_sent = models.DateField(verbose_name='Date Sent')

    class Meta:
        verbose_name_plural = 'Alerts'
        verbose_name = 'Alert'
        ordering = ['-date_sent', 'type']

    def __str__(self):
        return ', '.join([self.type, str(self.percent), str(self.date_sent)])


class Mode(models.Model):
    mode = models.CharField(max_length=10, verbose_name = 'Mode')

    class Meta:
        verbose_name_plural = 'Modes'
        verbose_name = 'Mode'

    def __str__(self):
        return self.mode
