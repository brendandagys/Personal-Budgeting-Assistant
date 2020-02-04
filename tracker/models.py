from django.db import models
import django_filters

import datetime
from django.utils import timezone

def current_date():
    return datetime.date.today()

def current_time():
    return str(timezone.now().time())[0:5]

class Purchase(models.Model):
    # null and blank arguments are False by default
    # null doesn't allow null in the database, blank is not database-related; it prevents '' in forms
    date = models.DateField(verbose_name='Date', default=current_date)
    time = models.CharField(max_length=20, verbose_name='Time (24 hr.)', default=current_time)
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')
    category = models.CharField(max_length=50, verbose_name='Category')
    item = models.CharField(max_length=100, verbose_name='Item(s)')
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        verbose_name_plural = 'Purchases'
        verbose_name = 'Purchase'

    def __str__(self):
        return ', '.join([str(self.date), self.time, self.category, self.item, str(self.amount)])

# class PurchaseFilter(django_filters.FilterSet):
#     category = django_filters.CharFilter(field_name='category', lookup_expr='iexact')

    # class Meta:
    #     model = Purchase
    #     fields = ['category']

class Filters(models.Model):
    last_update_date = models.DateField(verbose_name='Last Update Date', default=current_date)
    last_update_time = models.CharField(max_length=20, verbose_name = 'Time (24 hr.)', default=current_time)
    category_filter = models.CharField(max_length=20, verbose_name = 'Category Filter')
    time_filter = models.CharField(max_length=20, verbose_name = 'Time Filter')

    class Meta:
        verbose_name_plural = 'Filters'
        verbose_name = 'Filter'

    def __str__(self):
        return ', '.join([str(self.last_update_date), self.last_update_time])
