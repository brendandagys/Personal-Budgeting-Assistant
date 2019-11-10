from django.db import models

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
        verbose_name_plural = 'Purchase'
        verbose_name = 'Purchase'

    def __str__(self):
        return ', '.join([str(date), time, category, item, amount])
