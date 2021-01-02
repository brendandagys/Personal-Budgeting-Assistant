from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='User', related_name='purchase_categories')
    category = models.CharField(max_length=30, verbose_name='Category')
    threshold = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2, verbose_name='Threshold')
    threshold_rolling_days = models.PositiveIntegerField(default=30, verbose_name='Threshold Rolling Days')
    category_created_datetime = models.DateTimeField(auto_now_add=True, verbose_name='Category Created DateTime') # Any field with the auto_now attribute set will also inherit editable=False and won't show in admin panel

    class Meta:
        verbose_name_plural = 'Purchase Categories'
        verbose_name = 'Purchase Category'
        ordering = ['id']

    def __str__(self):
        return ', '.join([self.user.username, self.category, str(self.threshold), str(self.threshold_rolling_days) + ' days'])


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='User', related_name='purchases')
    date = models.DateField(verbose_name='Date', default=current_date)
    time = models.CharField(blank=True, default=current_time, max_length=5, verbose_name='Time (24 hr.)')
    item = models.CharField(max_length=100, verbose_name='Item(s)')
    category = models.ForeignKey(PurchaseCategory, null=True, on_delete=models.SET_NULL, verbose_name='Category', related_name='purchases_1') # blank=False by default...
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')
    category_2 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category 2', related_name='purchases_2')
    amount_2 = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2, verbose_name='Amount 2')
    description = models.TextField(blank=True, verbose_name='Details')
    currency = models.CharField(choices=CURRENCIES, default='CAD', max_length=10, verbose_name='Currency')
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Exchange Rate to CAD') # Default 1 unnecessary as we always run get_exchange_rate()
    receipt=models.FileField(blank=True, null=True, upload_to='media/', verbose_name='Receipt') # Eventually, switch to ImageField?

    class Meta:
        verbose_name_plural = 'Purchases'
        verbose_name = 'Purchase'

    def __str__(self):
        if self.category_2:
            return ', '.join([self.user.username, str(self.date), self.time, str(self.category.category), str(self.category_2.category), self.item, str(self.amount)])
        return ', '.join([self.user.username, str(self.date), self.time, str(self.category.category), self.item, str(self.amount)])


class Filter(models.Model):
    PAGES = [
        ('Homepage', 'Homepage'),
        ('Activity', 'Activity'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='User', related_name='filters')
    page = models.CharField(choices=PAGES, default='Activity', max_length=20, verbose_name='Page')
    category_filter_1 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 1', related_name='filters_1')
    category_filter_2 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 2', related_name='filters_2')
    category_filter_3 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 3', related_name='filters_3')
    category_filter_4 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 4', related_name='filters_4')
    category_filter_5 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 5', related_name='filters_5')
    category_filter_6 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 6', related_name='filters_6')
    category_filter_7 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 7', related_name='filters_7')
    category_filter_8 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 8', related_name='filters_8')
    category_filter_9 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 9', related_name='filters_9')
    category_filter_10 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 10', related_name='filters_10')
    category_filter_11 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 11', related_name='filters_11')
    category_filter_12 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 12', related_name='filters_12')
    category_filter_13 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 13', related_name='filters_13')
    category_filter_14 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 14', related_name='filters_14')
    category_filter_15 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 15', related_name='filters_15')
    category_filter_16 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 16', related_name='filters_16')
    category_filter_17 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 17', related_name='filters_17')
    category_filter_18 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 18', related_name='filters_18')
    category_filter_19 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 19', related_name='filters_19')
    category_filter_20 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 20', related_name='filters_20')
    category_filter_21 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 21', related_name='filters_21')
    category_filter_22 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 22', related_name='filters_22')
    category_filter_23 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 23', related_name='filters_23')
    category_filter_24 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 24', related_name='filters_24')
    category_filter_25 = models.ForeignKey(PurchaseCategory, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Category Filter 25', related_name='filters_25')
    start_date_filter = models.DateField(blank=True, null=True, verbose_name = 'Start Date')
    end_date_filter = models.DateField(blank=True, null=True, verbose_name = 'End Date')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Filter Last Updated')


    class Meta:
        verbose_name_plural = 'Filters'
        verbose_name = 'Filter'
        ordering = ['id']

    def __str__(self):
        return ', '.join([self.user.username, self.page, str(self.category_filter_1), str(self.start_date_filter), str(self.end_date_filter)])


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='User', related_name='accounts')
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
        return ', '.join([self.account])#, str(self.credit), str(self.active), str(self.account_created_datetime)])


class AccountUpdate(models.Model):
    account = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL, verbose_name='Account', related_name='account_updates')
    value = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Value')
    exchange_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Exchange Rate to CAD') # Default 1 unnecessary as we always run get_exchange_rate()
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Account Timestamp')

    class Meta:
        verbose_name_plural = 'Account Updates'
        verbose_name = 'Account Update'
        ordering = ['-timestamp']

    def __str__(self):
        return ', '.join([str(self.account), str(self.value), str(self.timestamp)])


class Recurring(models.Model):
    RECURRING_TYPES = [
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
    ]

    FREQUENCY_TYPES = [
        ('Date', 'Date'),
        ('Interval', 'Interval'),
        ('Xth Weekday', 'Xth Weekday'),
    ]

    INTERVAL_TYPES = [
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('Months', 'Months'),
    ]

    XTH_TYPES = [
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Weekday', 'Weekday'),
        ('Weekend', 'Weekend'),
    ]

    XTH_MODES = [
        ('General', 'General'),
        ('Specific', 'Specific'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='User', related_name='recurrings')
    name = models.CharField(max_length=40, verbose_name='Name')
    description = models.TextField(blank=True, verbose_name='Details')
    type = models.CharField(choices=RECURRING_TYPES, max_length=20, verbose_name='Type')
    account = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL, verbose_name='Account', related_name='recurrings')
    active = models.BooleanField(default=True, verbose_name='Active')
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Amount')

    start_date = models.DateField(default=current_date, verbose_name='Start Date')

    days = models.CharField(blank=True, max_length=100, verbose_name='Days')
    weekdays = models.CharField(blank=True, max_length=100, verbose_name='Weekdays')

    number = models.PositiveIntegerField(blank=True, null=True, default=30, verbose_name='Number')

    interval_type = models.CharField(blank=True, choices=INTERVAL_TYPES, max_length=15, verbose_name='Interval Type')

    xth_type = models.CharField(blank=True, choices=XTH_TYPES, max_length=15, verbose_name='Xth Type')
    xth_mode = models.CharField(blank=True, choices=XTH_MODES, max_length=15, verbose_name='Xth Mode')
    xth_after_specific_date = models.DateField(blank=True, null=True, verbose_name='Xth After Specific Date')
    xth_after_months = models.PositiveIntegerField(blank=True, null=True, verbose_name='Xth After Months')

    class Meta:
        verbose_name_plural = 'Recurrings'
        verbose_name = 'Recurring'
        ordering = ['-amount']

    def __str__(self):
        return ', '.join([self.user.username, self.name, self.type, self.account.account, str(self.active), str(self.amount)])


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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_to_use = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Account to Use', related_name='profiles_1')
    second_account_to_use = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Second Account to Use', related_name='profiles_2')
    third_account_to_use = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Third Account to Use', related_name='profiles_3')
    credit_account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Credit Account', related_name='profiles_4')
    debit_account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Debit Account', related_name='profiles_5')
    primary_currency = models.CharField(choices=CURRENCIES, default='CAD', max_length=10, verbose_name='Primary Currency')
    secondary_currency = models.CharField(choices=CURRENCIES, default='EUR', max_length=10, verbose_name='Secondary Currency')

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['user']

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
