from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage

from django.db.models import Q

# from django.contrib.auth.mixins import LoginRequiredMixin # Done in urls.py
from django.contrib.auth.decorators import login_required

from django.views import generic
from .forms import PurchaseForm, AccountForm, RecurringForm, QuickEntryForm, ProfileForm
from django.forms import modelformset_factory, NumberInput, TextInput, CheckboxInput, Select # Could have imported from .forms, if imported there
from .models import Purchase, QuickEntry, Filter, Recurring, Alert, PurchaseCategory, Account, AccountUpdate, Profile

from django.db.models import Sum

from math import floor
from decimal import Decimal
import datetime
import calendar
from dateutil.relativedelta import *
# import re # Was used in modelformset_factory, but then no longer needed
import pandas as pd

from forex_python.converter import CurrencyRates, CurrencyCodes
cr = CurrencyRates()
cc = CurrencyCodes()

def current_date():
    return datetime.date.today()

# Get information about today's date
# date = datetime.date.today()
# year = date.year
# month = date.month
# month_name = calendar.month_name[date.month]
# day = date.day
# weekday = date.weekday()


def information_page(request):
    return render(request, 'tracker/information_page.html')


def get_purchase_categories_tuples_list(user_object, start_date, end_date):
    # To generate the filter buttons on Purchase Category and provide context for the green_filters class
    purchase_categories_list = []
    # Only include the ones that have actually been used thus far by the user
    category_values_used = list(Purchase.objects.filter(user=user_object, date__gte=start_date, date__lte=end_date, category__isnull=False).values_list('category__category', flat=True).distinct())
    category_2_values_used = list(Purchase.objects.filter(user=user_object, date__gte=start_date, date__lte=end_date, category_2__isnull=False).values_list('category_2__category', flat=True).distinct())
    category_2_values_used = [x for x in category_2_values_used if x] # Remove None
    purchase_categories_list = sorted(list(set(category_values_used + category_2_values_used)))

    purchase_categories_tuples_list = []
    for index in range(0, len(purchase_categories_list), 2):
        if index != len(purchase_categories_list) - 1:
            purchase_categories_tuples_list.append((purchase_categories_list[index], purchase_categories_list[index+1]))
        else:
            purchase_categories_tuples_list.append((purchase_categories_list[index], ))

    return purchase_categories_tuples_list


def get_exchange_rate(foreign_currency, desired_currency):
    return Decimal(cr.get_rate(foreign_currency, desired_currency))


def convert_currency(foreign_value, foreign_currency, desired_currency):
    # foreign_value = account_value # account_value is actually for another currency
    conversion_rate = get_exchange_rate(foreign_currency, desired_currency)
    return round(foreign_value * conversion_rate, 2) # Convert the currency ... multiplying produces many decimal places, so must round (won't matter for model field, though)

@login_required
def get_quick_entries(request):
    user_object = request.user

    return JsonResponse({ 'quick_entries': list(QuickEntry.objects.filter(user=user_object).order_by('item').values()) })


@login_required
def account_update(request):
    if request.method == 'POST':
        user_object = request.user

        try: # Will fail if either credit or debit account isn't set, or if no AccountUpdates have yet been created
            if request.POST['id'][3:] == user_object.profile.credit_account.account: # If the Account updated was my credit card, check if the balance was paid off rather than added to
                credit_account_balance = AccountUpdate.objects.filter(account=user_object.profile.credit_account).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
                if Decimal(request.POST['value']) < credit_account_balance: # If the balance was paid off, the chequing account should be decremented
                    debit_account_balance = AccountUpdate.objects.filter(account=user_object.profile.debit_account).order_by('-timestamp').first().value
                    AccountUpdate.objects.create(account=user_object.profile.debit_account, value=debit_account_balance-(credit_account_balance - Decimal(request.POST['value'])), exchange_rate=get_exchange_rate(user_object.profile.debit_account.currency, 'CAD'))
                    dict.update({'id_' + user_object.profile.debit_account.account: '${:20,.2f}'.format(Decimal(debit_account_balance-(credit_account_balance - Decimal(request.POST['value']))))})
        except Exception:
            pass

        AccountUpdate.objects.create(account=Account.objects.get(user=user_object, account=request.POST['id'][3:]), value=request.POST['value'], exchange_rate=get_exchange_rate(Account.objects.get(user=user_object, account=request.POST['id'][3:]).currency, 'CAD')) # id is prefixed with 'id_'

        return JsonResponse({})


@login_required
def reset_credit_card(request): # This function won't run unless both are defined, because the button is disabled if so
    user_object = request.user

    debit_account_balance = AccountUpdate.objects.filter(account=user_object.profile.debit_account).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
    credit_account_balance = AccountUpdate.objects.filter(account=user_object.profile.credit_account).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
    AccountUpdate.objects.create(account=user_object.profile.credit_account, value=0, exchange_rate=get_exchange_rate(user_object.profile.credit_account.currency, 'CAD'))
    AccountUpdate.objects.create(account=user_object.profile.debit_account, value=debit_account_balance-credit_account_balance, exchange_rate=get_exchange_rate(user_object.profile.debit_account.currency, 'CAD'))

    return JsonResponse({'debit_account': request.user.profile.debit_account.account,
                         'credit_account': request.user.profile.credit_account.account,
                         'debit_account_balance': '${:20,.2f}'.format(debit_account_balance-credit_account_balance)}, safe=False)


@login_required
def get_accounts_sum(request):
    user_object = request.user

    accounts_sum = 0

    for account in Account.objects.filter(user=user_object, active=True):
        account_value = 0 if AccountUpdate.objects.filter(account=account, account__active=True).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=account, account__active=True).order_by('-timestamp').first().value
        account_value*=-1 if account.credit else 1 # If a 'credit' account, change sign before summing with the cumulative total

        if account.currency != 'CAD':
            foreign_value = account_value
            account_value = convert_currency(account_value, account.currency, 'CAD')

            # Different currency symbol formatting for American dollars
            USD_suffix = ''
            if account.currency == 'USD':
                USD_suffix = ' USD'

            print('Account \'{}\' converted from {}{}{} to ${} CAD.'.format(account.account, cc.get_symbol(account.currency), foreign_value, USD_suffix, account_value))

        accounts_sum+=account_value


    CAD_USD_rate = cc.get_symbol('USD') + str(round(get_exchange_rate('CAD', 'USD'), 3))
    CAD_EUR_rate = cc.get_symbol('EUR') + str(round(get_exchange_rate('CAD', 'EUR'), 3))

    USD_CAD_rate = '$' + str(round(get_exchange_rate('USD', 'CAD'), 3))
    EUR_CAD_rate = '$' + str(round(get_exchange_rate('EUR', 'CAD'), 3))

    return JsonResponse({'accounts_sum': '${:20,.2f}'.format(accounts_sum),
                         'exchange_rates': { 'CAD_USD': CAD_USD_rate, 'CAD_EUR': CAD_EUR_rate, 'USD_CAD': USD_CAD_rate, 'EUR_CAD': EUR_CAD_rate },
                         'accounts_form': str(AccountForm(user_object)),
    }, safe=False)


@login_required
def get_json_queryset(request):
    user_object = request.user

    filter_instance = Filter.objects.get(user=user_object, page='Activity') # get_or_create() run in PurchaseListView get_context_data()

    start_date_filter = filter_instance.start_date_filter
    end_date_filter = filter_instance.end_date_filter

    if start_date_filter is None:
        if Purchase.objects.filter(user=user_object).order_by('date').first() is not None: # Date of first purchase recorded
            start_date_filter = Purchase.objects.filter(user=user_object).order_by('date').first().date # Date of first purchase recorded
        else:
            start_date_filter = current_date()

    if end_date_filter is None:
        if Purchase.objects.filter(user=user_object).order_by('date').last() is not None: # Date of last purchase recorded
            end_date_filter = Purchase.objects.filter(user=user_object).order_by('date').last().date # Date of last purchase recorded
        else:
            end_date_filter = current_date()

    days_difference = (end_date_filter - start_date_filter).days + 1

    purchase_categories_list = [x.id for x in [filter_instance.category_filter_1, filter_instance.category_filter_2, filter_instance.category_filter_3, filter_instance.category_filter_4, filter_instance.category_filter_5,
                                               filter_instance.category_filter_6, filter_instance.category_filter_7, filter_instance.category_filter_8, filter_instance.category_filter_9, filter_instance.category_filter_10,
                                               filter_instance.category_filter_11, filter_instance.category_filter_12, filter_instance.category_filter_13, filter_instance.category_filter_14, filter_instance.category_filter_15,
                                               filter_instance.category_filter_16, filter_instance.category_filter_17, filter_instance.category_filter_18, filter_instance.category_filter_19, filter_instance.category_filter_20,
                                               filter_instance.category_filter_21, filter_instance.category_filter_22, filter_instance.category_filter_23, filter_instance.category_filter_24, filter_instance.category_filter_25]
                                               if x is not None]

    periods = []
    sums = []

    maximum_amount = 10000000 if filter_instance.maximum_amount is None else filter_instance.maximum_amount
    search_string = request.GET.get('search_string', '')

    periods_queryset = Purchase.objects.select_related('category', 'category_2').filter((Q(category__in=purchase_categories_list) | Q(category_2__in=purchase_categories_list)) & (Q(item__icontains=search_string) | Q(description__icontains=search_string)), user=user_object, amount__lt=maximum_amount).exclude(date=filter_instance.date_to_exclude)

    for x in range(1, 5):
        temp_start_date = start_date_filter-datetime.timedelta(days=x*days_difference)
        temp_end_date = start_date_filter-datetime.timedelta(days=x*days_difference)+datetime.timedelta(days=days_difference-1)
        periods.append('{} - {}'.format(temp_start_date, temp_end_date))

        temp_queryset = periods_queryset.filter(date__gte=temp_start_date, date__lte=temp_end_date).values_list('category', 'category_2', 'amount', 'amount_2') # Returns a Queryset of tuples

        # Get the total cost of all of the purchases
        past_purchases_sum = 0
        for purchase in temp_queryset:
            if purchase[0] in purchase_categories_list: # If first category matches, always add 'amount'
                past_purchases_sum+=purchase[2]
            if purchase[1] in purchase_categories_list: # If second category matches...
                if purchase[3] is not None: # If there is a second value, always add it
                    past_purchases_sum+=purchase[3]
                elif purchase[0] not in purchase_categories_list: # If no 'amount_2', and first category DIDN'T match (we don't want to double-count), add 'amount' (in this case first three of tuple are populated)
                    past_purchases_sum+=purchase[2]
        sums.append(past_purchases_sum)

    periods.reverse()
    sums.reverse()

    # print(days_difference)
    # print(periods)
    # print(sums)

    maximum_amount = 10000000 if filter_instance.maximum_amount is None else filter_instance.maximum_amount

    queryset_data = Purchase.objects.filter((Q(category__in=purchase_categories_list) | Q(category_2__in=purchase_categories_list)) & (Q(item__icontains=search_string) | Q(description__icontains=search_string)), user=user_object, amount__lt=maximum_amount, date__gte=start_date_filter, date__lte=end_date_filter).exclude(date=filter_instance.date_to_exclude).order_by('-date', '-time', 'category__category', 'item')

    purchases_list = list(queryset_data.values('id', 'date', 'time', 'item', 'category__category', 'amount', 'category_2__category', 'amount_2', 'description', 'receipt')) # List of dictionaries

    for dict in purchases_list:
        # Convert the stored path (media/image.png) to the full URL, and add to the object dict
        # if dict['receipt'] is not None: # May not have a receipt file
        try:
            dict['url'] = request.build_absolute_uri(Purchase.objects.get(id=dict['id']).receipt.url)#.replace('static/', '') # For some reason, this was appearing before the 'media/' prefix, and S3 was giving a Key Error
        # else:
        except Exception:
            dict['url'] = ''

    # Get the total cost of all of the purchases
    purchases_sum = 0
    for purchase in list(queryset_data.values_list('category', 'category_2', 'amount', 'amount_2')): # Returns a Queryset of tuples
        if purchase[0] in purchase_categories_list: # If first category matches, always add 'amount'
            purchases_sum+=purchase[2]
        if purchase[1] in purchase_categories_list: # If second category matches...
            if purchase[3] is not None: # If there is a second value, always add it
                purchases_sum+=purchase[3]
            elif purchase[0] not in purchase_categories_list: # If no 'amount_2', and first category DIDN'T match (we don't want to double-count), add 'amount' (in this case first three of tuple are populated)
                purchases_sum+=purchase[2]


    # Savings rate
    start_accounts_value = 0
    end_accounts_value = 0


    queryset = AccountUpdate.objects.select_related('account').filter(account__user=user_object, account__active=True) # Ordered by -timestamp

    accounts_list = [Account.objects.get(id=x) for x in set(queryset.values_list('account', flat=True))] # List of distinct Account objects that have ever had an update...
    for account in accounts_list:
        try:
            if account.credit:
                start_accounts_value-=AccountUpdate.objects.filter(account=account, timestamp__gte=start_date_filter).order_by('timestamp').first().value
                end_accounts_value-=AccountUpdate.objects.filter(account=account, timestamp__lte=end_date_filter).order_by('-timestamp').first().value
            else:
                start_accounts_value+=AccountUpdate.objects.filter(account=account, timestamp__gte=start_date_filter).order_by('timestamp').first().value
                end_accounts_value+=AccountUpdate.objects.filter(account=account, timestamp__lte=end_date_filter).order_by('-timestamp').first().value
        except Exception:
            pass

    try: # Divide by zero error on new account creation
        savings_rate = 'SAVINGS: ' + str(round((100 * (end_accounts_value - start_accounts_value - purchases_sum))/(end_accounts_value - start_accounts_value), 2)) + '%'
    except Exception:
        savings_rate = 'SAVINGS: N/A'

    print(start_accounts_value)
    print(end_accounts_value)
    print(savings_rate)

    return JsonResponse({'data': purchases_list,
                         'purchases_sum': '${:20,.2f}'.format(purchases_sum),
                         'past_periods': {'labels': periods, 'values': sums},
                         'categories_count': len(purchase_categories_list),
                         'purchase_category_tuples': get_purchase_categories_tuples_list(user_object, start_date_filter, end_date_filter),
                         'savings_rate': {'start': '{:20,.2f}'.format(start_accounts_value), 'end': '{:20,.2f}'.format(end_accounts_value), 'rate': savings_rate},
    }, safe=False)


@login_required # Don't think this is necessary
def get_purchases_chart_data(request):

    if request.method == 'GET':
        user_object = request.user

        filter_instance = Filter.objects.get(user=user_object, page='Homepage')

        start_date_filter = filter_instance.start_date_filter
        end_date_filter = filter_instance.end_date_filter

        print('Start date filter: ' + str(start_date_filter))
        print('End date filter: ' + str(end_date_filter))

        if start_date_filter is None or start_date_filter < Purchase.objects.filter(user=user_object).order_by('date').first().date:
            if Purchase.objects.filter(user=user_object).order_by('date').first() is not None: # Date of first purchase recorded
                start_date_filter = Purchase.objects.filter(user=user_object).order_by('date').first().date # Date of first purchase recorded
            else:
                start_date_filter = current_date()


        if end_date_filter is None or end_date_filter > Purchase.objects.filter(user=user_object).order_by('date').last().date:
            if Purchase.objects.filter(user=user_object).order_by('date').last() is not None: # Date of first purchase recorded
                end_date_filter = Purchase.objects.filter(user=user_object).order_by('date').last().date # Date of first purchase recorded
            else:
                end_date_filter = current_date()

        print(start_date_filter)
        print(end_date_filter)

        print('Days on chart: ' + str((end_date_filter-start_date_filter).days))

        # Extract the current filter values
        category_filter_1 = filter_instance.category_filter_1; category_filter_2 = filter_instance.category_filter_2
        category_filter_3 = filter_instance.category_filter_3; category_filter_4 = filter_instance.category_filter_4
        category_filter_5 = filter_instance.category_filter_5; category_filter_6 = filter_instance.category_filter_6
        category_filter_7 = filter_instance.category_filter_7; category_filter_8 = filter_instance.category_filter_8
        category_filter_9 = filter_instance.category_filter_9; category_filter_10 = filter_instance.category_filter_10
        category_filter_11 = filter_instance.category_filter_11; category_filter_12 = filter_instance.category_filter_12
        category_filter_13 = filter_instance.category_filter_13; category_filter_14 = filter_instance.category_filter_14
        category_filter_15 = filter_instance.category_filter_15; category_filter_16 = filter_instance.category_filter_16
        category_filter_17 = filter_instance.category_filter_17; category_filter_18 = filter_instance.category_filter_18
        category_filter_19 = filter_instance.category_filter_19; category_filter_20 = filter_instance.category_filter_20
        category_filter_21 = filter_instance.category_filter_21; category_filter_22 = filter_instance.category_filter_22
        category_filter_23 = filter_instance.category_filter_23; category_filter_24 = filter_instance.category_filter_24
        category_filter_25 = filter_instance.category_filter_25

        # Make a list of the currently applied filters
        current_filter_list = [x.category if x is not None else x for x in [category_filter_1, category_filter_2, category_filter_3, category_filter_4, category_filter_5, category_filter_6, category_filter_7, category_filter_8, category_filter_9, category_filter_10,
                       category_filter_11, category_filter_12, category_filter_13, category_filter_14, category_filter_15, category_filter_16, category_filter_17, category_filter_18, category_filter_19, category_filter_20,
                       category_filter_21, category_filter_22, category_filter_23, category_filter_24, category_filter_25]]
        current_filter_list_unique = sorted(list(set([x for x in current_filter_list if x])))
        current_filter_list_unique_ids = [PurchaseCategory.objects.get(user=user_object, category=x).id for x in current_filter_list_unique] # To filter the Queryset below, we need to give a list of IDs to the category fields, as it's a foreign key
        print('Filters for chart: ' + str(current_filter_list_unique))

        queryset = Purchase.objects.select_related('category', 'category_2').filter(Q(category__in=current_filter_list_unique_ids) | Q(category_2__in=current_filter_list_unique_ids), user=user_object, date__gte=start_date_filter, date__lte=end_date_filter).exclude(date=filter_instance.date_to_exclude).values('date', 'category', 'category_2', 'amount', 'amount_2')

        def get_period_sum(queryset, start_date, end_date):
            # If the first PurchaseCategory matches, always add amount_1 to the total
            sum_1 = 0 if queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
            # If the second PurchaseCategory matches AND amount_2 is given, always add amount_2 to the total
            sum_2 = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__gt=0, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__gt=0, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum']
            # If the second PurchaseCategory matches AND amount_2 is not given AND first PurchaseCategory didn't match (avoid double-counting), add amount_1 to the total
            sum_3 = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__isnull=True, date__gte=start_date, date__lte=end_date).exclude(category__in=current_filter_list_unique_ids).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__isnull=True, date__gte=start_date, date__lte=end_date).exclude(category__in=current_filter_list_unique_ids).aggregate(Sum('amount'))['amount__sum']

            return sum_1 + sum_2 + sum_3 if filter_instance.maximum_amount is None or sum_1 + sum_2 + sum_3 <= filter_instance.maximum_amount else 0


        # DAILY CHART
        labels_daily = []
        values_daily = []

        for datetime_index in pd.date_range(start_date_filter, end_date_filter, freq='D'): # freq='D' is default; returns a DateTime index
            labels_daily.append(str(datetime_index.date()) + '  (' + calendar.day_name[datetime_index.weekday()][:2] + ')')

        for date in labels_daily:
            date = date[:-6] # Remove the prefix we just added so we can filter with the date

            sum_1 = 0 if queryset.filter(category__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount'))['amount__sum']
            sum_2 = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__gt=0, date=date).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__gt=0, date=date).aggregate(Sum('amount_2'))['amount_2__sum']
            sum_3 = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__isnull=True, date=date).exclude(category__in=current_filter_list_unique_ids).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, amount_2__isnull=True, date=date).exclude(category__in=current_filter_list_unique_ids).aggregate(Sum('amount'))['amount__sum']

            values_daily.append(sum_1 + sum_2 + sum_3 if filter_instance.maximum_amount is None or sum_1 + sum_2 + sum_3 <= filter_instance.maximum_amount else 0)


        # WEEKLY CHART
        dates_list = pd.date_range(start=start_date_filter, end=end_date_filter, freq='7D').strftime('%Y-%m-%d').tolist() # This will be a DateTimeIndex. Last two methods format the dates into strings and turn into a list
        if dates_list[-1] != str(end_date_filter):
            dates_list.append(str(end_date_filter)) # Ensure we get all data up to the end_date_filter, even if the interval leaves a remainder

        labels_weekly = []
        values_weekly = []

        for date in dates_list: # If the last date is greater than end_date_filter, change it to end_date_filter, add the label, and end loop
            end_date = str(datetime.datetime.strptime(date, '%Y-%m-%d').date()+datetime.timedelta(days=6))
            if date == str(end_date_filter): # Prevent showing a range like '01-01 - 01-01'. Instead, just show one date
                labels_weekly.append(date)
                break
            if end_date >= str(end_date_filter): # Make sure that the very last date is no greater than end_date_filter
                labels_weekly.append(date + ' - ' + str(end_date_filter))
                break
            labels_weekly.append(date + ' - ' + end_date)

        for date_range in labels_weekly:
            if ' - ' in date_range:
                start_date, end_date = date_range.split(' - ')
            else:
                start_date, end_date = (date_range, date_range)

            values_weekly.append(get_period_sum(queryset, start_date, end_date))

        labels_weekly = [x[5:10] + ' - ' + x[-5:] if ' - ' in x else x[5:] for x in labels_weekly] # Removing the year component, as the label is too long


        # BI-WEEKLY CHART
        dates_list = pd.date_range(start=start_date_filter, end=end_date_filter, freq='14D').strftime('%Y-%m-%d').tolist() # This will be a DateTimeIndex. Last two methods format the dates into strings and turn into a list
        if dates_list[-1] != str(end_date_filter):
            dates_list.append(str(end_date_filter)) # Ensure we get all data up to the end_date_filter, even if the interval leaves a remainder

        labels_biweekly = []
        values_biweekly = []

        for date in dates_list: # If the last date is greater than end_date_filter, change it to end_date_filter, add the label, and end loop
            end_date = str(datetime.datetime.strptime(date, '%Y-%m-%d').date()+datetime.timedelta(days=13))
            if date == str(end_date_filter): # Prevent showing a range like '01-01 - 01-01'. Instead, just show one date
                labels_biweekly.append(date)
                break
            if end_date >= str(end_date_filter): # Make sure that the very last date is no greater than end_date_filter
                labels_biweekly.append(date + ' - ' + str(end_date_filter))
                break
            labels_biweekly.append(date + ' - ' + end_date)

        for date_range in labels_biweekly:
            if ' - ' in date_range:
                start_date, end_date = date_range.split(' - ')
            else:
                start_date, end_date = (date_range, date_range)

            values_biweekly.append(get_period_sum(queryset, start_date, end_date))

        labels_biweekly = [x[5:10] + ' - ' + x[-5:] if ' - ' in x else x[5:] for x in labels_biweekly] # Removing the year component, as the label is too long


        # MONTHLY CHART
        dates_list = [start_date_filter] # List of datetime objects
        start_date_monthly = start_date_filter
        while start_date_monthly < end_date_filter: # Using pd.date_range() with freq = 'M', '1M', 'MS' all did not work!
            start_date_monthly+=relativedelta(months=+1)
            if start_date_monthly < end_date_filter:
                dates_list.append(start_date_monthly)
            else:
                dates_list.append(end_date_filter)
                break

        labels_monthly = []
        values_monthly = []

        for date in dates_list: # If the last date is greater than end_date_filter, change it to end_date_filter, add the label, and end loop
            end_date = date+relativedelta(months=+1)+relativedelta(days=-1)
            if date == end_date_filter:
                labels_monthly.append(str(date))
                break
            if end_date >= end_date_filter:
                labels_monthly.append(str(date) + ' - ' + str(end_date_filter))
                break
            labels_monthly.append(str(date) + ' - ' + str(end_date))

        for date_range in labels_monthly:
            if ' - ' in date_range:
                start_date, end_date = date_range.split(' - ')
            else:
                start_date, end_date = (date_range, date_range)

            values_monthly.append(get_period_sum(queryset, start_date, end_date))

        labels_monthly = [x[5:10] + ' - ' + x[-5:] if ' - ' in x else x[5:] for x in labels_monthly] # Removing the year component, as the label is too long


        return JsonResponse({'labels_daily': labels_daily,
                             'values_daily': values_daily,
                             'labels_weekly': labels_weekly,
                             'values_weekly': values_weekly,
                             'labels_biweekly': labels_biweekly,
                             'values_biweekly': values_biweekly,
                             'labels_monthly': labels_monthly,
                             'values_monthly': values_monthly,
                             'purchase_category_tuples': get_purchase_categories_tuples_list(user_object, start_date_filter, end_date_filter),
        })


@login_required
def get_net_worth_chart_data(request):
    user_object = request.user

    labels = []
    values = []
    print(request.GET)
    if request.GET['account'] == 'All':
        queryset = AccountUpdate.objects.select_related('account').filter(account__user=user_object, account__active=True) # Ordered by -timestamp
    else:
        queryset = AccountUpdate.objects.select_related('account').filter(account__user=user_object, account__active=True, account=Account.objects.get(id=request.GET['account']))

    distinct_accounts_list = [Account.objects.get(id=x) for x in set(queryset.values_list('account', flat=True))] # List of distinct Account objects that have ever had an update...

    latest_value_dict = {} # When an Account has no update on a certain date, the queryset will return None; we will then take the most-recent account value
    for account in distinct_accounts_list:
        latest_value_dict[account.account] = 0

    try: # None object has no attribute timestamp
        for datetime_index in pd.date_range(queryset.last().timestamp.date(), queryset.first().timestamp.date(), freq='D'): # freq='D' is default; returns a DateTime index
            labels.append(str(datetime_index.date()) + '  (' + calendar.day_name[datetime_index.weekday()][:2] + ')')
    except Exception:
        pass

    for date in labels:
        start_date = date[:-6] # Remove the suffix we just added so we can filter with the date
        end_date = str(datetime.datetime.strptime(date[:-6], '%Y-%m-%d').date()+datetime.timedelta(days=1))

        queryset_one_date = queryset.filter(timestamp__gte=start_date, timestamp__lt=end_date) # Has all AccountUpdates on one given date

        accounts_sum = 0

        for account_object in distinct_accounts_list: # List of objects

            last_account_update_on_date = queryset_one_date.filter(account=account_object).order_by('-timestamp').first()
            if last_account_update_on_date is None: # If there is no update on that specific date...
                last_account_value_on_date = latest_value_dict[account_object.account]
            else:
                last_account_value_on_date = last_account_update_on_date.value
                if account_object.credit:
                    last_account_value_on_date*=-1 # If a 'credit' account, change sign before summing with the cumulative total

                if account_object.currency != 'CAD':
                    foreign_value = last_account_value_on_date
                    last_account_value_on_date = convert_currency(last_account_value_on_date, account_object.currency, 'CAD')

                latest_value_dict[account_object.account] = last_account_value_on_date

            accounts_sum+=last_account_value_on_date

        values.append(accounts_sum)

    return JsonResponse({'labels': labels, 'values': values})


@login_required
def get_pie_chart_data(request):
    user_object = request.user

    data_dict = { 'pie_labels': (), 'pie_values': () }

    filter_instance = Filter.objects.get(user=user_object, page='Activity')

    purchase_categories_list = [x.category for x in [filter_instance.category_filter_1, filter_instance.category_filter_2, filter_instance.category_filter_3, filter_instance.category_filter_4, filter_instance.category_filter_5,
                                                     filter_instance.category_filter_6, filter_instance.category_filter_7, filter_instance.category_filter_8, filter_instance.category_filter_9, filter_instance.category_filter_10,
                                                     filter_instance.category_filter_11, filter_instance.category_filter_12, filter_instance.category_filter_13, filter_instance.category_filter_14, filter_instance.category_filter_15,
                                                     filter_instance.category_filter_16, filter_instance.category_filter_17, filter_instance.category_filter_18, filter_instance.category_filter_19, filter_instance.category_filter_20,
                                                     filter_instance.category_filter_21, filter_instance.category_filter_22, filter_instance.category_filter_23, filter_instance.category_filter_24, filter_instance.category_filter_25]
                                                     if x is not None]

    if len(purchase_categories_list) > 0:

        start_date_filter = filter_instance.start_date_filter
        end_date_filter = filter_instance.end_date_filter

        if start_date_filter is None:
            if Purchase.objects.filter(user=user_object).order_by('date').first() is not None: # Date of first purchase recorded
                start_date_filter = Purchase.objects.filter(user=user_object).order_by('date').first().date # Date of first purchase recorded
            else:
                start_date_filter = current_date()

        if end_date_filter is None:
            if Purchase.objects.filter(user=user_object).order_by('date').last() is not None: # Date of first purchase recorded
                end_date_filter = Purchase.objects.filter(user=user_object).order_by('date').last().date # Date of first purchase recorded
            else:
                end_date_filter = current_date()


        maximum_amount = 10000000 if filter_instance.maximum_amount is None else filter_instance.maximum_amount
        search_string = request.GET.get('search_string', '')

        queryset = Purchase.objects.select_related('category', 'category_2').filter(Q(item__icontains=search_string) | Q(description__icontains=search_string), user=user_object, amount__lt=maximum_amount, date__gte=start_date_filter, date__lte=end_date_filter).exclude(date=filter_instance.date_to_exclude)

        pie_data = []

        if filter_instance.pie_chart_mode == 'Counts':
            mode = 'counts'
            for category in purchase_categories_list:
                pie_data.append((category, queryset.filter(Q(category__category=category) | Q(category_2__category=category)).count()))

        elif filter_instance.pie_chart_mode == 'Counts Percents':
            mode = 'counts_percents'
            total = queryset.filter(Q(category__category__in=purchase_categories_list) | Q(category_2__category__in=purchase_categories_list)).count()
            for category in purchase_categories_list:
                pie_data.append((category, round(100 * queryset.filter(Q(category__category=category) | Q(category_2__category=category)).count()/total, 2)))

        elif filter_instance.pie_chart_mode == 'Sums':
            mode = 'sums'
            for category in purchase_categories_list:
                sum_1 = queryset.filter(Q(category__category=category, amount__isnull=False)).aggregate(Sum('amount'))['amount__sum'] if len(queryset.filter(Q(category__category=category, amount__isnull=False))) > 0 else 0
                sum_2 = queryset.filter(Q(category_2__category=category, amount__isnull=True, amount_2__isnull=False)).aggregate(Sum('amount_2'))['amount_2__sum'] if len(queryset.filter(Q(category_2__category=category, amount__isnull=True, amount_2__isnull=False))) > 0 else 0
                sum_3 = queryset.filter(Q(category_2__category=category, amount_2__isnull=True)).aggregate(Sum('amount'))['amount__sum'] if len(queryset.filter(Q(category_2__category=category, amount_2__isnull=True))) > 0 else 0
                pie_data.append((category, round(sum_1 + sum_2 + sum_3, 2)))

        elif filter_instance.pie_chart_mode == 'Sums Percents':
            mode = 'sums_percents'
            total_1 = queryset.filter(Q(category__category__in=purchase_categories_list) | Q(category_2__category__in=purchase_categories_list)).aggregate(Sum('amount'))['amount__sum'] if queryset.filter(Q(category__category__in=purchase_categories_list) | Q(category_2__category__in=purchase_categories_list)).aggregate(Sum('amount'))['amount__sum'] else 0
            total_2 = queryset.filter(Q(category__category__in=purchase_categories_list) | Q(category_2__category__in=purchase_categories_list)).aggregate(Sum('amount_2'))['amount_2__sum'] if queryset.filter(Q(category__category__in=purchase_categories_list) | Q(category_2__category__in=purchase_categories_list)).aggregate(Sum('amount_2'))['amount_2__sum'] else 0
            total = total_1 + total_2

            for category in purchase_categories_list:
                sum_1 = queryset.filter(Q(category__category=category, amount__isnull=False)).aggregate(Sum('amount'))['amount__sum'] if len(queryset.filter(Q(category__category=category, amount__isnull=False))) > 0 else 0
                sum_2 = queryset.filter(Q(category_2__category=category, amount__isnull=True, amount_2__isnull=False)).aggregate(Sum('amount_2'))['amount_2__sum'] if len(queryset.filter(Q(category_2__category=category, amount__isnull=True, amount_2__isnull=False))) > 0 else 0
                sum_3 = queryset.filter(Q(category_2__category=category, amount_2__isnull=True)).aggregate(Sum('amount'))['amount__sum'] if len(queryset.filter(Q(category_2__category=category, amount_2__isnull=True))) > 0 else 0
                pie_data.append((category, round(100 * (sum_1 + sum_2 + sum_3)/total, 2)))

        pie_data.sort(key=lambda x: x[1], reverse=True) # Reverse-sort the list of tuples by the second values: the counts
        pie_data = list(zip(*pie_data[:7])) # Only keep seven, for readability | * is unpacking operator | is a list of two tuples

        data_dict.update({ 'pie_labels': pie_data[0], 'pie_values': pie_data[1], 'mode': mode })

    return JsonResponse(data_dict)


@login_required
def delete_purchase(request):
    user_object = request.user
    purchase_object = Purchase.objects.get(id=request.POST['id'])

    account_updates = AccountUpdate.objects.filter(purchase__id=request.POST['id'])

    if len(account_updates) > 0:
        last_account_update_value = AccountUpdate.objects.filter(account=purchase_object.account).order_by('-timestamp').first().value
        purchase_amount = purchase_object.amount + (0 if purchase_object.amount_2 is None else purchase_object.amount_2) # Brackets were needed

        if purchase_object.account.credit:
            amended_account_value = last_account_update_value - purchase_amount
        else:
            amended_account_value = last_account_update_value + purchase_amount

        AccountUpdate.objects.create(account=purchase_object.account, value=amended_account_value, exchange_rate=get_exchange_rate(purchase_object.account.currency, 'CAD'))

    purchase_object.delete()
    print('\nDeleted Purchase: ' + str(request.POST['id']) + '\n')

    return HttpResponse()


@login_required
def homepage(request):
    user_object = request.user

    if request.method == 'GET':
        context = {}

        threshold_dict = {}

        colors = ['bg-success', 'bg-primary', 'bg-info']
        use_color = 3

        for category in PurchaseCategory.objects.filter(user=user_object, threshold__isnull=False, threshold__gt=0):
            color_to_use = colors[use_color%3]
            use_color+=1

            queryset = Purchase.objects.filter(Q(category=category) | Q(category_2=category), date__gte=current_date()-datetime.timedelta(days=category.threshold_rolling_days)).order_by('date')
            sum_1 = 0 if queryset.filter(category=category).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category=category).aggregate(Sum('amount'))['amount__sum']
            sum_2 = 0 if queryset.filter(category_2=category, amount_2__gt=0).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2=category, amount_2__gt=0).aggregate(Sum('amount_2'))['amount_2__sum']
            sum_3 = 0 if queryset.filter(category_2=category, amount_2__isnull=True).exclude(category=category).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category_2=category, amount_2__isnull=True).exclude(category=category).aggregate(Sum('amount'))['amount__sum']

            threshold_dict[category] = (category.category, round(100 * (sum_1 + sum_2 + sum_3)/category.threshold, 1), category.threshold, category.threshold_rolling_days, color_to_use, '' if queryset.first() is None else '| ' + str(queryset.first().date))

        context['purchase_category_dict'] = threshold_dict

        context['account_to_use'] = user_object.profile.account_to_use # None, if not set
        context['account_to_use_currency'] = context['account_to_use'].currency if context['account_to_use'] else None
        context['second_account_to_use'] = user_object.profile.second_account_to_use
        context['second_account_to_use_currency'] = context['second_account_to_use'].currency if context['second_account_to_use'] else None
        context['third_account_to_use'] = user_object.profile.third_account_to_use
        context['third_account_to_use_currency'] = context['third_account_to_use'].currency if context['third_account_to_use'] else None

        context['primary_currency'] = user_object.profile.primary_currency

        # Create a filter object if this user hasn't loaded any pages yet
        filter_instance = Filter.objects.get_or_create(user=user_object, page='Homepage')[0] # Returns a tuple (object, True/False depending on whether or not just created)

        context['start_date'] = '' if filter_instance.start_date_filter is None else str(filter_instance.start_date_filter)
        context['end_date'] = '' if filter_instance.end_date_filter is None else str(filter_instance.end_date_filter)
        context['date_to_exclude'] = '' if filter_instance.date_to_exclude is None else str(filter_instance.date_to_exclude)
        context['maximum_amount'] = '' if filter_instance.maximum_amount is None else str(filter_instance.maximum_amount)

        check_recurring_payments(request)

    elif request.method == 'POST':

        purchase_form = PurchaseForm(request.POST, request.FILES)
        # print(purchase_form.errors)
        # print(request.FILES)
        purchase_instance = Purchase()

        if purchase_form.is_valid():
            purchase_instance.user = user_object
            purchase_instance.date = purchase_form.cleaned_data['date']
            purchase_instance.time = purchase_form.cleaned_data['time'] # Cleaning done in forms.py
            purchase_instance.item = purchase_form.cleaned_data['item'].strip()
            purchase_instance.category = purchase_form.cleaned_data['category'] # Pretty sure that passing an integer (which is coming from the front-end) representing the id means you don't have to retrieve an actual object
            purchase_instance.amount = purchase_form.cleaned_data['amount']
            purchase_instance.category_2 = purchase_form.cleaned_data['category_2']
            purchase_instance.amount_2 = purchase_form.cleaned_data['amount_2']
            purchase_instance.description = purchase_form.cleaned_data['description'].strip() if len(purchase_form.cleaned_data['description'].strip()) == 0 or purchase_form.cleaned_data['description'].strip()[-1] in ['.', '!', '?'] else purchase_form.cleaned_data['description'].strip() + '.' # Add a period if not present
            purchase_instance.currency = purchase_form.cleaned_data['currency']
            purchase_instance.exchange_rate = get_exchange_rate(purchase_form.cleaned_data['currency'], 'CAD')
            purchase_instance.receipt = request.FILES['receipt'] if len(request.FILES) > 0 and request.FILES['receipt'].size < 50000001 else None # Make sure file was uploaded, and check size (also done in front-end)

            # If an account to charge was available, and chosen in front-end, create the appropriate AccountUpdate object...
            account_object_to_charge = Account.objects.get(user=user_object, account=purchase_form.cleaned_data['account_to_use']) if purchase_form.cleaned_data['account_to_use'] != '' else None
            purchase_instance.account = account_object_to_charge

            purchase_instance.save()


            if account_object_to_charge:
                account_balance = AccountUpdate.objects.filter(account=account_object_to_charge).order_by('-timestamp').first().value

                # Deal with the 2nd amount, which may be None
                amount_2 = 0
                if purchase_instance.amount_2 is not None:
                    amount_2 = purchase_instance.amount_2

                amount_to_charge = purchase_instance.amount + amount_2

                if account_object_to_charge.credit: # True if a credit account
                    amount_to_charge*=-1

                AccountUpdate.objects.create(account=account_object_to_charge, purchase=purchase_instance, value=account_balance-amount_to_charge, exchange_rate=purchase_instance.exchange_rate)


            return redirect('homepage')


    # This returns a blank form, (to clear for the next submission if request.method == 'POST')
    purchase_form = PurchaseForm()

    context['purchase_form'] = purchase_form


    return render(request, 'tracker/homepage.html', context=context)


class PurchaseListView(generic.ListView):
    # queryset = Purchase.objects.order_by('-date')
    # context_object_name = 'purchase_list'
    template_name = 'tracker/activity.html' # Specify your own template


    def get_queryset(self):
        pass


    def get_context_data(self, *args, **kwargs):
        user_object = self.request.user

        # Call the base implementation first to get a context
        context = super().get_context_data(*args, **kwargs) # Simply using context = {} works, but being safe...

        # To generate fields for me to update account balances
        context['account_form'] = AccountForm(user_object)

        context['debit_account'] = 'Not set'
        if user_object.profile.debit_account:
            context['debit_account'] = user_object.profile.debit_account.account

        context['credit_account'] = 'Not set'
        if user_object.profile.credit_account:
            context['credit_account'] = user_object.profile.credit_account.account

        # To fill the datepickers with the current date filters and label the active filters. Create a filter object if this user hasn't loaded any pages yet
        filter_instance = Filter.objects.get_or_create(user=user_object, page='Activity')[0] # Returns a tuple (object, True/False depending on whether or not just created)

        context['start_date'] = '' if filter_instance.start_date_filter is None else str(filter_instance.start_date_filter)
        context['end_date'] = '' if filter_instance.end_date_filter is None else str(filter_instance.end_date_filter)
        context['date_to_exclude'] = '' if filter_instance.date_to_exclude is None else str(filter_instance.date_to_exclude)
        context['maximum_amount'] = '' if filter_instance.maximum_amount is None else str(filter_instance.maximum_amount)

        context['purchase_category_filters'] = [x.category for x in [filter_instance.category_filter_1, filter_instance.category_filter_2, filter_instance.category_filter_3, filter_instance.category_filter_4, filter_instance.category_filter_5,
                                                                     filter_instance.category_filter_6, filter_instance.category_filter_7, filter_instance.category_filter_8, filter_instance.category_filter_9, filter_instance.category_filter_10,
                                                                     filter_instance.category_filter_11, filter_instance.category_filter_12, filter_instance.category_filter_13, filter_instance.category_filter_14, filter_instance.category_filter_15,
                                                                     filter_instance.category_filter_16, filter_instance.category_filter_17, filter_instance.category_filter_18, filter_instance.category_filter_19, filter_instance.category_filter_20,
                                                                     filter_instance.category_filter_21, filter_instance.category_filter_22, filter_instance.category_filter_23, filter_instance.category_filter_24, filter_instance.category_filter_25]
                                                                     if x is not None]

        # context['purchase_categories_tuples_list'] = get_purchase_categories_tuples_list(user_object)

        net_worth_chart_options = '<option value="All">All Accounts</option>'
        for account in Account.objects.filter(user=user_object, active=True):
            net_worth_chart_options+='<option value="{0}">{1}</option>'.format(account.id, account.account)
        context['net_worth_chart_options'] = net_worth_chart_options

        context['display_reset_credit_card'] = False if user_object.profile.credit_account is None or user_object.profile.debit_account is None else True

        return context


@login_required
def settings(request):
    user_object = request.user

    if request.method == 'GET':
        if 'type' in request.GET:
            if request.GET['model'] == 'Profile':
                choices = '<option value>---------</option>'
                debit_choices = '<option value>---------</option>'
                credit_choices = '<option value>---------</option>'
                for x in Account.objects.filter(user=user_object, active=True).values('id', 'account', 'credit'): # Using a generator or list comprehension wasn't working
                    choices+='<option value="{0}">{1}</option>'.format(x['id'], x['account'])

                    if x['credit'] is True:
                        credit_choices+='<option value="{0}">{1}</option>'.format(x['id'], x['account'])
                    else:
                        debit_choices+='<option value="{0}">{1}</option>'.format(x['id'], x['account'])

                return JsonResponse({'choices': choices,
                                     'debit_choices': debit_choices,
                                     'credit_choices': credit_choices,
                                     'values': {'account_to_use': '' if user_object.profile.account_to_use is None else user_object.profile.account_to_use.id,
                                                'second_account_to_use': '' if user_object.profile.second_account_to_use is None else user_object.profile.second_account_to_use.id,
                                                'third_account_to_use': '' if user_object.profile.third_account_to_use is None else user_object.profile.third_account_to_use.id,
                                                'credit_account': '' if user_object.profile.credit_account is None else user_object.profile.credit_account.id,
                                                'debit_account': '' if user_object.profile.debit_account is None else user_object.profile.debit_account.id,
                                                'primary_currency': user_object.profile.primary_currency,
                                    } })

            elif request.GET['model'] == 'Recurring':
                table_string = '''
<table id="recurring_table" style="table-layout:fixed; margin:auto; max-width:500px;" class="table table-sm table-striped table-bordered">
    <tr style="font-size:0.4rem; text-align:center;">
        <th>Name</th>
        <th style="width:11%">Type</th>
        <th>Account</th>
        <th>Category</th>
        <th style="width:11%">Active</th>
        <th style="width:13.5%">Amount</th>
        <th>Freq.</th>
    </tr>
'''

                for object in Recurring.objects.select_related('account', 'category').filter(user=user_object).values('name', 'type', 'account__account', 'category__category', 'active', 'amount'):
                    table_string+='''
    <tr class="hover" style="font-size:0.3rem; text-align:center;">
        <td style="vertical-align:middle;">{0}</td>
        <td style="vertical-align:middle;">{1}</td>
        <td style="vertical-align:middle;">{2}</td>
        <td style="vertical-align:middle;">{3}</td>
        <td style="vertical-align:middle;">{4}</td>
        <td style="vertical-align:middle;">{5}</td>
        <td style="vertical-align:middle;">{6}</td>
    </tr>
'''.format(object['name'], object['type'], str(object['account__account']).replace('None', ''), str(object['category__category']).replace('None', ''), object['active'], object['amount'], '')
                return JsonResponse(table_string + '</table>', safe=False)

            elif request.GET['model'] == 'Quick Entry':
                count = 0

                table_string = '''
<table style="table-layout:fixed; margin:auto; max-width:500px;" class="table table-sm table-striped table-bordered">
    <tr style="font-size:0.4rem; text-align:center;">
        <th style="width:7%">ID</th>
        <th>Category</th>
        <th>Item</th>
        <th style="width:13.5%">Amount</th>
        <th>Category 2</th>
        <th style="width:13.5%">Amount 2</th>
        <th>Specifics</th>
    </tr>
'''

                for object in QuickEntry.objects.select_related('category', 'category_2').filter(user=user_object).values('id', 'category__category', 'item', 'amount', 'category_2__category', 'amount_2', 'description'):
                    count+=1
                    table_string+='''
    <tr style="font-size:0.3rem; text-align:center;">
        <td style="vertical-align:middle;">{0}</td>
        <td style="vertical-align:middle;">{1}</td>
        <td style="vertical-align:middle;">{2}</td>
        <td style="vertical-align:middle;">{3}</td>
        <td style="vertical-align:middle;">{4}</td>
        <td style="vertical-align:middle;">{5}</td>
        <td style="vertical-align:middle;">{6}</td>
    </tr>
'''.format(str(object['id']), str(object['category__category']).replace('None', ''), object['item'], object['amount'], str(object['category_2__category']).replace('None', ''), str(object['amount_2']).replace('None', ''), object['description'])
                return JsonResponse({ 'table_string': table_string + '</table>', 'count': count }, safe=False)


        else: # Inital page load
            context = {}

            ThresholdFormSet = modelformset_factory(PurchaseCategory,
                                                    fields=('id', 'category', 'threshold', 'threshold_rolling_days'),
                                                    widgets={'category': TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:180px;'}),
                                                             'threshold': NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:95px;', 'inputmode': 'decimal'}),
                                                             'threshold_rolling_days': NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:53px;', 'inputmode': 'numeric'})})

            AccountFormSet = modelformset_factory(Account,
                                                  exclude=(),
                                                  widgets={'account': TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:200px;'}),
                                                           'credit': CheckboxInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:15px; margin:auto;'}),
                                                           'currency': Select(attrs={'class': 'form-control form-control-sm', 'style': 'width:67px; margin:auto;'}),
                                                           'active': CheckboxInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:15px; margin:auto;'})})

            context['threshold_formset'] = ThresholdFormSet(queryset=PurchaseCategory.objects.filter(user=user_object))

            context['account_formset'] = AccountFormSet(queryset=Account.objects.filter(user=user_object))

            context['recurring_list'] = Recurring.objects.select_related('account', 'category').filter(user=user_object).values('name', 'type', 'account__account', 'category__category', 'active', 'amount')
            context['recurring_form'] = RecurringForm()

            # context['quick_entry_list'] = QuickEntry.objects.select_related('category, category_2').filter(user=user_object).values('id', 'category__category', 'item', 'amount', 'category_2__category', 'amount_2', 'description')
            context['quick_entry_form'] = QuickEntryForm()

            profile_form_data = {'account_to_use': user_object.profile.account_to_use.id if user_object.profile.account_to_use is not None else None,
                                 'second_account_to_use': user_object.profile.second_account_to_use.id if user_object.profile.second_account_to_use is not None else None,
                                 'third_account_to_use': user_object.profile.third_account_to_use.id if user_object.profile.third_account_to_use is not None else None,
                                 'credit_account': user_object.profile.credit_account.id if user_object.profile.credit_account is not None else None,
                                 'debit_account': user_object.profile.debit_account.id if user_object.profile.debit_account is not None else None,
                                 'primary_currency': user_object.profile.primary_currency, }

            context['profile_form'] = ProfileForm(profile_form_data)

            context['purchase_category_count'] = PurchaseCategory.objects.filter(user=user_object).count()
            context['account_count'] = Account.objects.filter(user=user_object).count() # Don't require it to be active, because we still want to be able to delete all accounts
            context['recurring_count'] = Recurring.objects.filter(user=user_object).count()
            context['quick_entry_count'] = QuickEntry.objects.filter(user=user_object).count()

            return render(request, 'tracker/settings.html', context=context)


    elif request.method == 'POST':
        data_dict = {}
        # print(request.POST)
        if request.POST['type'] == 'Submit':
            if request.POST['model'] == 'Quick Entry':
                quick_entry_form = QuickEntryForm(request.POST)

                if quick_entry_form.is_valid():
                    quick_entry_instance = QuickEntry()

                    quick_entry_instance.user = user_object
                    quick_entry_instance.item = quick_entry_form.cleaned_data['item'].strip()
                    quick_entry_instance.category = quick_entry_form.cleaned_data['category']
                    quick_entry_instance.amount = quick_entry_form.cleaned_data['amount']
                    quick_entry_instance.category_2 = quick_entry_form.cleaned_data['category_2']
                    quick_entry_instance.amount_2 = quick_entry_form.cleaned_data['amount_2']
                    quick_entry_instance.description = quick_entry_form.cleaned_data['description'].strip() if len(quick_entry_form.cleaned_data['description'].strip()) == 0 or quick_entry_form.cleaned_data['description'].strip()[-1] == '.' else quick_entry_form.cleaned_data['description'].strip() + '.' # Add a period if not present

                    quick_entry_instance.save()

            elif request.POST['model'] == 'Recurring Payment':
                    recurring_instance = Recurring()

                    recurring_instance.user = user_object
                    recurring_instance.name = request.POST['name'].strip()
                    recurring_instance.description = request.POST['description'].strip()
                    recurring_instance.type = request.POST['recurring_type']
                    recurring_instance.account = Account.objects.get(id=request.POST['account'])
                    recurring_instance.category = PurchaseCategory.objects.get(id=request.POST['category'])
                    recurring_instance.active = True if request.POST['active'] == 'true' else False
                    recurring_instance.amount = request.POST['amount']
                    recurring_instance.start_date = request.POST['start_date']
                    recurring_instance.dates = request.POST['dates']
                    recurring_instance.weekdays = request.POST['weekdays']
                    recurring_instance.number = None if request.POST['number'] == '' else request.POST['number']
                    recurring_instance.interval_type = request.POST['interval_type']
                    recurring_instance.xth_type = request.POST['xth_type']
                    recurring_instance.xth_from_specific_date = request.POST['xth_from_specific_date']
                    recurring_instance.xth_after_months = None if request.POST['xth_after_months'] == '' else request.POST['xth_after_months']

                    recurring_instance.save()

        elif request.POST['type'] == 'Delete': # ALL ARE TRIMMED in the front-end!
            if request.POST['model'] == 'Purchase Category':
                to_delete = PurchaseCategory.objects.filter(user=user_object, category=request.POST['to_delete'])
            elif request.POST['model'] == 'Account':
                to_delete = Account.objects.filter(user=user_object, account=request.POST['to_delete'])
            elif request.POST['model'] == 'Recurring Payment':
                to_delete = Recurring.objects.filter(user=user_object, name=request.POST['to_delete'])
            elif request.POST['model'] == 'Quick Entry':
                to_delete = QuickEntry.objects.filter(user=user_object, id=request.POST['to_delete'])

            # Filter will always run, so throw an error if no items to delete were found
            if to_delete.count() > 0:
                to_delete.delete()
            else:
                raise Exception('No items to delete!')

        elif request.POST['type'] == 'Update':
            if request.POST['model'] == 'Profile':
                if request.POST['value'].isdigit(): # request.POST['value'] is a string
                    setattr(user_object.profile, request.POST['id'][3:], Account.objects.get(id=request.POST['value']))
                else:
                    setattr(user_object.profile, request.POST['id'][3:], None if request.POST['value'] == '' else request.POST['value'])
                user_object.save()

            elif request.POST['model'] == 'Purchase Category':
                if request.POST['id'] == '': # This is the bottom, blank row. Won't have an ID, so create a new object
                    purchase_category_object = PurchaseCategory.objects.create(user=user_object)
                    data_dict.update({'id': purchase_category_object.id})
                else: # Otherwise, get the PurchaseCategory and update the appropriate attribute
                    purchase_category_object = PurchaseCategory.objects.get(id=request.POST['id'])
                if request.POST['field'] == 'threshold':
                    value = Decimal(request.POST['value'])
                elif request.POST['field'] == 'threshold_rolling_days':
                    value = int(request.POST['value'])
                else: # Field is 'category'
                    value = request.POST['value']
                setattr(purchase_category_object, request.POST['field'], value)
                purchase_category_object.save()

            elif request.POST['model'] == 'Account':
                if request.POST['id'] == '':
                    account_object = Account.objects.create(user=user_object)
                    data_dict.update({'id': account_object.id})
                else:
                    account_object = Account.objects.get(id=request.POST['id'])

                if request.POST['field'] == 'account':
                    value = request.POST['value']
                elif request.POST['field'] == 'credit': # .val() comes through as 'on' for checkboxes. Use .is(':checked') ... but easier to toggle here
                    value = not(account_object.credit)
                elif request.POST['field'] == 'currency':
                    value = request.POST['value']
                else: # Field is 'active'
                    value = not(account_object.active)
                setattr(account_object, request.POST['field'], value)

                # If an Account is deactivated, make sure it's removed from Profile options
                if not(account_object.active):
                    if user_object.profile.account_to_use == account_object:
                        user_object.profile.account_to_use = None
                    if user_object.profile.second_account_to_use == account_object:
                        user_object.profile.second_account_to_use = None
                    if user_object.profile.third_account_to_use == account_object:
                        user_object.profile.third_account_to_use = None

                    user_object.save()

                account_object.save()

            elif request.POST['model'] == 'Recurring Payment':
                recurring_queryset = Recurring.objects.filter(name=request.POST['name'])
                for object in recurring_queryset:
                    if object.active:
                        object.active = False
                    else:
                        object.active = True
                    object.save()

            return JsonResponse(data_dict) # Only needed for update, to return an ID of the row for Purchase Category and Account
        return HttpResponse()


@login_required
def filter_manager(request):
    user_object = request.user

    if request.method == 'GET' and request.GET['page'] == 'Activity' or request.method == 'POST' and request.POST['page'] == 'Activity': # GET must be first!
        filter_instance = Filter.objects.get(user=user_object, page='Activity')
    else:
        filter_instance = Filter.objects.get(user=user_object, page='Homepage')

    if request.method == 'POST' and request.POST['type'] not in ['Date', 'Mode'] or request.method == 'GET': # We need these for any GET request, and obviously not for POST requests for the date filters
        # Generate a comprehensive list of PurchaseCategories
        full_category_filter_list = []
        for purchase_category in PurchaseCategory.objects.filter(user=user_object):
            full_category_filter_list.append(purchase_category.category)
        full_category_filter_list.sort()
        print('Full category filter list: ' + str(full_category_filter_list))

        # Extract the current filter values
        category_filter_1 = filter_instance.category_filter_1; category_filter_2 = filter_instance.category_filter_2
        category_filter_3 = filter_instance.category_filter_3; category_filter_4 = filter_instance.category_filter_4
        category_filter_5 = filter_instance.category_filter_5; category_filter_6 = filter_instance.category_filter_6
        category_filter_7 = filter_instance.category_filter_7; category_filter_8 = filter_instance.category_filter_8
        category_filter_9 = filter_instance.category_filter_9; category_filter_10 = filter_instance.category_filter_10
        category_filter_11 = filter_instance.category_filter_11; category_filter_12 = filter_instance.category_filter_12
        category_filter_13 = filter_instance.category_filter_13; category_filter_14 = filter_instance.category_filter_14
        category_filter_15 = filter_instance.category_filter_15; category_filter_16 = filter_instance.category_filter_16
        category_filter_17 = filter_instance.category_filter_17; category_filter_18 = filter_instance.category_filter_18
        category_filter_19 = filter_instance.category_filter_19; category_filter_20 = filter_instance.category_filter_20
        category_filter_21 = filter_instance.category_filter_21; category_filter_22 = filter_instance.category_filter_22
        category_filter_23 = filter_instance.category_filter_23; category_filter_24 = filter_instance.category_filter_24
        category_filter_25 = filter_instance.category_filter_25

        # Make a list of the currently applied filters
        current_filter_list = [x.category if x is not None else x for x in [category_filter_1, category_filter_2, category_filter_3, category_filter_4, category_filter_5, category_filter_6, category_filter_7, category_filter_8, category_filter_9, category_filter_10,
                       category_filter_11, category_filter_12, category_filter_13, category_filter_14, category_filter_15, category_filter_16, category_filter_17, category_filter_18, category_filter_19, category_filter_20,
                       category_filter_21, category_filter_22, category_filter_23, category_filter_24, category_filter_25]]
        current_filter_list_unique = sorted(list(set([x for x in current_filter_list if x])))
        print('Originally applied filters: ' + str(current_filter_list_unique))

    # Tells the pages which Purchase Category filters should be styled
    if request.method == 'GET': # DATE FILTER VALUES ARE SENT IN homepage() and PurchaseListView() ! No need here.
        if len(current_filter_list_unique) == len(full_category_filter_list):
            current_filter_list_unique.append('All Categories')
        return JsonResponse(current_filter_list_unique, safe=False)

    elif request.method == 'POST':

        if request.POST['type'] == 'Date':
            filter_value = request.POST['filter_value'] # Only present in date-related AJAX calls

            if filter_value == '':
                filter_value = None

            if request.POST['id'] == 'datepicker':
                filter_instance.start_date_filter = filter_value
            elif request.POST['id'] == 'datepicker_2':
                filter_instance.end_date_filter = filter_value

            filter_instance.save()

            return HttpResponse()

        elif request.POST['type'] == 'Extra Filters':
            if request.POST['id'] == 'date_to_exclude':
                if request.POST['filter_value'] == '':
                    filter_instance.date_to_exclude = None
                else:
                    filter_instance.date_to_exclude = request.POST['filter_value']
            elif request.POST['id'] == 'maximum_amount':
                filter_instance.maximum_amount = None if request.POST['filter_value'] == '' else request.POST['filter_value']

            filter_instance.save()

            return HttpResponse()

        elif request.POST['type'] == 'Mode':
            if request.POST['id'] == 'category_counts':
                filter_instance.pie_chart_mode = 'Counts'
            elif request.POST['id'] == 'category_sums':
                filter_instance.pie_chart_mode = 'Sums'
            elif request.POST['id'] == 'category_counts_percents':
                filter_instance.pie_chart_mode = 'Counts Percents'
            elif request.POST['id'] == 'category_sums_percents':
                filter_instance.pie_chart_mode = 'Sums Percents'

            filter_instance.save()

            return HttpResponse()

        elif request.POST['type'] == 'Category':
            # Get the filter that was clicked
            filter_value = request.POST['id'] # The filter 'value' is simply stored in the ID
            print('Clicked filter value: ' + str(filter_value))

            def set_filters(filter_list):
                reset_filters()

                try:
                    filter_instance.category_filter_1 = None if filter_list[0] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[0])
                    filter_instance.category_filter_2 = None if filter_list[1] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[1])
                    filter_instance.category_filter_3 = None if filter_list[2] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[2])
                    filter_instance.category_filter_4 = None if filter_list[3] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[3])
                    filter_instance.category_filter_5 = None if filter_list[4] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[4])
                    filter_instance.category_filter_6 = None if filter_list[5] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[5])
                    filter_instance.category_filter_7 = None if filter_list[6] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[6])
                    filter_instance.category_filter_8 = None if filter_list[7] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[7])
                    filter_instance.category_filter_9 = None if filter_list[8] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[8])
                    filter_instance.category_filter_10 = None if filter_list[9] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[9])
                    filter_instance.category_filter_11 = None if filter_list[10] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[10])
                    filter_instance.category_filter_12 = None if filter_list[11] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[11])
                    filter_instance.category_filter_13 = None if filter_list[12] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[12])
                    filter_instance.category_filter_14 = None if filter_list[13] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[13])
                    filter_instance.category_filter_15 = None if filter_list[14] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[14])
                    filter_instance.category_filter_16 = None if filter_list[15] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[15])
                    filter_instance.category_filter_17 = None if filter_list[16] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[16])
                    filter_instance.category_filter_18 = None if filter_list[17] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[17])
                    filter_instance.category_filter_19 = None if filter_list[18] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[18])
                    filter_instance.category_filter_20 = None if filter_list[19] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[19])
                    filter_instance.category_filter_21 = None if filter_list[20] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[20])
                    filter_instance.category_filter_22 = None if filter_list[21] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[21])
                    filter_instance.category_filter_23 = None if filter_list[22] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[22])
                    filter_instance.category_filter_24 = None if filter_list[23] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[23])
                    filter_instance.category_filter_25 = None if filter_list[24] is None else PurchaseCategory.objects.get(user=user_object, category=filter_list[24])
                except: # If list passed in is not long enough...
                    pass

                filter_instance.save()

            def reset_filters():
                filter_instance.category_filter_1 = None; filter_instance.category_filter_2 = None; filter_instance.category_filter_3 = None
                filter_instance.category_filter_4 = None; filter_instance.category_filter_5 = None; filter_instance.category_filter_6 = None
                filter_instance.category_filter_7 = None; filter_instance.category_filter_8 = None; filter_instance.category_filter_9 = None
                filter_instance.category_filter_10 = None; filter_instance.category_filter_11 = None; filter_instance.category_filter_12 = None
                filter_instance.category_filter_13 = None; filter_instance.category_filter_14 = None; filter_instance.category_filter_15 = None
                filter_instance.category_filter_16 = None; filter_instance.category_filter_17 = None; filter_instance.category_filter_18 = None
                filter_instance.category_filter_19 = None; filter_instance.category_filter_20 = None; filter_instance.category_filter_21 = None
                filter_instance.category_filter_22 = None; filter_instance.category_filter_23 = None; filter_instance.category_filter_24 = None
                filter_instance.category_filter_25 = None

                filter_instance.save()


            # Clear filter values if necessary
            if filter_value == 'All Categories':
                reset_filters()
                if len(current_filter_list_unique) == len(full_category_filter_list) or len(current_filter_list_unique) == 25: # For when you've just clicked 'All Categories'
                    return JsonResponse([], safe=False) # safe=False necessary for non-dict objects to be serialized
                else:
                    set_filters(full_category_filter_list)
                    if len(full_category_filter_list) < 26:
                        full_category_filter_list.append('All Categories')
                    return JsonResponse(full_category_filter_list, safe=False) # safe=False necessary for non-dict objets to be serialized

            else:
                if len(current_filter_list_unique) == 25:
                    reset_filters()
                    return JsonResponse([], safe=False) # safe=False necessary for non-dict objects to be serialized

                else: # Otherwise, there's an available slot...
                    if filter_value in current_filter_list_unique:
                        current_filter_list_unique.remove(filter_value)
                    else:
                        current_filter_list_unique.append(filter_value)

                    current_filter_list_unique.sort()
                    print('New applied filter list: ' + str(current_filter_list_unique))

                    set_filters(current_filter_list_unique)

                    if len(current_filter_list_unique) == len(full_category_filter_list):
                        current_filter_list_unique.append('All Categories')

                    return JsonResponse(current_filter_list_unique, safe=False) # safe=False necessary for non-dict objects to be serialized

@login_required
def check_recurring_payments(request):
    user_object = request.user

    recurrings = Recurring.objects.filter(user=user_object, active=True, category__isnull=False) # If a Category was deleted, this mandatory field will be None and fail below when creating the Purchase

    for x in recurrings:
        latest_entry = Purchase.objects.filter(user=user_object, item=x.name).order_by('-date').first()
        date_to_iterate_from = latest_entry.date if latest_entry is not None else x.start_date

        if x.dates != '' or x.weekdays != '':
            # Get all of the permissible dates/weekdays to add bills
            acceptable_dates = [] # Will contain strings
            if x.dates is not None:
                acceptable_dates+=x.dates.split(',')
            if x.weekdays is not None:
                acceptable_dates+=x.weekdays.split(',')

            try: # Not exactly needed, but cleaner...
                acceptable_dates.remove('') # Returns nothing
            except Exception:
                pass

            # Iterate through each date, from last bill OR start date, to the current date
            for date in pd.date_range(start=date_to_iterate_from, end=current_date()).strftime('%Y-%m-%d').tolist(): # This will be a DateTimeIndex. Last two methods format the dates into strings and turn into a list
                date = datetime.datetime.strptime(date, '%Y-%m-%d')
                latest_account_value = 0 if AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first().value

                # If it's an appropriate date, AND the bill hasn't already been recorded on this day...create a Purchase and AccountUpdate
                if (str(date.day) in acceptable_dates or calendar.day_name[date.weekday()] in acceptable_dates) and len(Purchase.objects.filter(user=user_object, item=x.name, date=date)) == 0:
                    purchase_object = Purchase.objects.create(
                        user=user_object,
                        date=date,
                        time='00:00',
                        item=x.name,
                        category=x.category,
                        amount=x.amount,
                        description=x.description,
                        account=x.account,
                        exchange_rate=1,
                    )
                    print('Created Purchase for: ' + x.name + ', on date: ' + str(date)[0:10])

                    AccountUpdate.objects.create(
                        account=x.account,
                        value=(latest_account_value + x.amount) if x.account.credit else (latest_account_value - x.amount),
                        exchange_rate=get_exchange_rate(x.account.currency, 'CAD'),
                        purchase=purchase_object,
                    )
                    print('Created AccountUpdate for: ' + x.name + ', in Account: ' + x.account.account)


        elif x.interval_type != '':
            while date_to_iterate_from <= current_date():
                latest_account_value = 0 if AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first().value

                if len(Purchase.objects.filter(user=user_object, item=x.name, date=date_to_iterate_from)) == 0:
                    purchase_object = Purchase.objects.create(
                        user=user_object,
                        date=date_to_iterate_from,
                        time='00:00',
                        item=x.name,
                        category=x.category,
                        amount=x.amount,
                        description=x.description,
                        account=x.account,
                        exchange_rate=1,
                    )
                    print('Created Purchase for: ' + x.name + ', on date: ' + str(date_to_iterate_from)[0:10])

                    AccountUpdate.objects.create(
                        account=x.account,
                        value=(latest_account_value + x.amount) if x.account.credit else (latest_account_value - x.amount),
                        exchange_rate=get_exchange_rate(x.account.currency, 'CAD'),
                        purchase=purchase_object,
                    )
                    print('Created AccountUpdate for: ' + x.name + ', in Account: ' + x.account.account)

                # Increment for the next date to check
                if x.interval_type == 'Days':
                    date_to_iterate_from+=datetime.timedelta(days=x.number)
                elif x.interval_type == 'Weeks':
                    date_to_iterate_from+=datetime.timedelta(days=7 * x.number)
                elif x.interval_type == 'Months':
                    date_to_iterate_from+=relativedelta(months=+1)


        elif x.xth_type != '':
            # print(3)
            # print(x)

            type_to_day_dict = {
                'Monday': MO,
                'Tuesday': TU,
                'Wednesday': WE,
                'Thursday': TH,
                'Friday': FR,
                'Saturday': SA,
                'Sunday': SU,
            }

            months = 1 if x.xth_after_months is None else x.xth_after_months

            while date_to_iterate_from <= current_date():
                latest_account_value = 0 if AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=x.account).order_by('-timestamp').first().value

                if len(Purchase.objects.filter(user=user_object, item=x.name, date=date_to_iterate_from)) == 0:
                    purchase_object = Purchase.objects.create(
                        user=user_object,
                        date=date_to_iterate_from,
                        time='00:00',
                        item=x.name,
                        category=x.category,
                        amount=x.amount,
                        description=x.description,
                        account=x.account,
                        exchange_rate=1,
                    )
                    print('Created Purchase for: ' + x.name + ', on date: ' + str(date_to_iterate_from)[0:10])

                    AccountUpdate.objects.create(
                        account=x.account,
                        value=(latest_account_value + x.amount) if x.account.credit else (latest_account_value - x.amount),
                        exchange_rate=get_exchange_rate(x.account.currency, 'CAD'),
                        purchase=purchase_object,
                    )
                    print('Created AccountUpdate for: ' + x.name + ', in Account: ' + x.account.account)

                if x.xth_type not in ['Weekday', 'Weekend']:
                    date_to_iterate_from+=relativedelta(months=+months, day=int(x.xth_from_specific_date), weekday=type_to_day_dict[x.xth_type](x.number))
                elif x.xth_type == 'Weekday':
                    date_to_iterate_from+=relativedelta(months=+months, day=int(x.xth_from_specific_date))
                    while date_to_iterate_from.weekday() not in [0, 1, 2, 3, 4]:
                        date_to_iterate_from+=datetime.timedelta(days=1)
                elif x.th_type == 'Weekend':
                    date_to_iterate_from+=relativedelta(months=+months, day=int(x.xth_from_specific_date))
                    while date_to_iterate_from.weekday() not in [5, 6]:
                        date_to_iterate_from+=datetime.timedelta(days=1)
