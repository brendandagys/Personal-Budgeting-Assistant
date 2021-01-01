from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage

from django.db.models import Q

# from django.contrib.auth.mixins import LoginRequiredMixin # Done in urls.py
from django.contrib.auth.decorators import login_required

from django.views import generic
from .forms import PurchaseForm, AccountForm, RecurringForm
from django.forms import modelformset_factory, NumberInput, TextInput, CheckboxInput, Select # Could have imported from .forms, if imported there
from .models import Purchase, Filter, Recurring, Alert, Mode, PurchaseCategory, Account, AccountUpdate

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
date = datetime.date.today()
year = date.year
month = date.month
month_name = calendar.month_name[date.month]
day = date.day
weekday = date.weekday()


def get_purchase_categories_tuples_list():
    # To generate the filter buttons on Purchase Category and provide context for the green_filters class
    purchase_categories_list = []
    # Only include the ones that have actually been used thus far
    category_values_used = list(Purchase.objects.all().values_list('category', flat=True).distinct())
    category_2_values_used = list(Purchase.objects.all().values_list('category_2', flat=True).distinct())
    category_2_values_used = [x for x in category_2_values_used if x] # Remove None
    purchase_categories_used = list(set(category_values_used + category_2_values_used))

    [purchase_categories_list.append(PurchaseCategory.objects.get(id=x).category) for x in purchase_categories_used]
    purchase_categories_list.sort()

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
def account_update(request):
    if request.method == 'POST':
        dict = { request.POST['id']: '${:20,.2f}'.format(Decimal(request.POST['value'])) }

        if request.POST['id'][3:] == '3': # If the Account updated was my credit card, check if the balance was paid off rather than added to
            credit_card_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=3)).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
            if Decimal(request.POST['value']) < credit_card_balance: # If the balance was paid off, the chequing account should be decremented
                chequing_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=1)).order_by('-timestamp').first().value
                AccountUpdate.objects.create(account=Account.objects.get(pk=1), value=chequing_balance-(credit_card_balance - Decimal(request.POST['value'])), exchange_rate=1)
                dict.update({'id_1': '${:20,.2f}'.format(Decimal(chequing_balance-(credit_card_balance - Decimal(request.POST['value']))))})

        account = Account.objects.get(pk=request.POST['id'][3:])
        AccountUpdate.objects.create(account=account, value=request.POST['value'], exchange_rate=get_exchange_rate(account.currency, 'CAD')) # id is prefixed with 'id_'

        return JsonResponse(dict)


@login_required
def reset_credit_card(request):
    chequing_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=1)).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
    credit_card_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=3)).order_by('-timestamp').first().value # Order should be preserved from models.py Meta options, but being safe
    AccountUpdate.objects.create(account=Account.objects.get(id=3), value=0, exchange_rate=1)
    AccountUpdate.objects.create(account=Account.objects.get(id=1), value=chequing_balance-credit_card_balance, exchange_rate=1)
    return JsonResponse('${:20,.2f}'.format(chequing_balance-credit_card_balance), safe=False)


@login_required
def get_accounts_sum(request):
    accounts_sum = 0

    for account in Account.objects.all():
        account_value = 0 if AccountUpdate.objects.filter(account=account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=account).order_by('-timestamp').first().value
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


    USD_rate = cc.get_symbol('USD') + str(round(get_exchange_rate('CAD', 'USD'), 3))
    EUR_rate = cc.get_symbol('EUR') + str(round(get_exchange_rate('CAD', 'EUR'), 3))

    return JsonResponse({ 'accounts_sum': '${:20,.2f}'.format(accounts_sum), 'exchange_rates': { 'USD': USD_rate, 'EUR': EUR_rate } }, safe=False)


@login_required
def get_json_queryset(request):
    filter_instance = Filter.objects.first()

    start_date_filter = filter_instance.start_date_filter
    end_date_filter = filter_instance.end_date_filter

    if start_date_filter is None:
        start_date_filter = '2019-01-01'

    if end_date_filter is None:
        end_date_filter = '2099-12-31'

    purchase_categories_list = [x.id for x in [filter_instance.category_filter_1, filter_instance.category_filter_2, filter_instance.category_filter_3, filter_instance.category_filter_4, filter_instance.category_filter_5,
                                               filter_instance.category_filter_6, filter_instance.category_filter_7, filter_instance.category_filter_8, filter_instance.category_filter_9, filter_instance.category_filter_10,
                                               filter_instance.category_filter_11, filter_instance.category_filter_12, filter_instance.category_filter_13, filter_instance.category_filter_14, filter_instance.category_filter_15,
                                               filter_instance.category_filter_16, filter_instance.category_filter_17, filter_instance.category_filter_18, filter_instance.category_filter_19, filter_instance.category_filter_20,
                                               filter_instance.category_filter_21, filter_instance.category_filter_22, filter_instance.category_filter_23, filter_instance.category_filter_24, filter_instance.category_filter_25]
                                               if x is not None]

    queryset_data = Purchase.objects.filter(Q(date__gte=start_date_filter) & Q(date__lte=end_date_filter) & (Q(category__in=purchase_categories_list) | Q(category_2__in=purchase_categories_list))).order_by('-date', '-time')

    purchases_list = list(queryset_data.values()) # List of dictionaries

    # Fill a dictionary with the mappings from id to category, as in the front-end only the id would show because it's a foreign key
    purchase_category_dict = {}
    for object in PurchaseCategory.objects.all().values('id', 'category'): # Queryset of dicts
        purchase_category_dict[object['id']] = object['category']
    # Update the id for each PurchaseCategory with the category name
    for dict in purchases_list:
        dict['category_id'] = purchase_category_dict[dict['category_id']]
        if dict['category_2_id'] is not None:
            dict['category_2_id'] = purchase_category_dict[dict['category_2_id']]

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
        if purchase[0] in purchase_categories_list:
            purchases_sum+=purchase[2]
        if purchase[1] in purchase_categories_list and purchase[3] is not None: # Will be None when no value is given
            purchases_sum+=purchase[3]

    return JsonResponse({'data': purchases_list, 'purchases_sum': '${:20,.2f}'.format(purchases_sum)}, safe=False)


@login_required # Don't think this is necessary
def get_chart_data(request):

    if request.method == 'GET':

        filter_instance = Filter.objects.last() # First is for Purchases page

        start_date_filter = filter_instance.start_date_filter
        end_date_filter = filter_instance.end_date_filter

        print('Start date filter: ' + str(start_date_filter))
        print('End date filter: ' + str(end_date_filter))

        if start_date_filter is None or start_date_filter < Purchase.objects.all().order_by('date').first().date:
            start_date_filter = Purchase.objects.all().order_by('date').first().date # Date of first purchase recorded

        if end_date_filter is None:
            end_date_filter = current_date()

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
        current_filter_list_unique_ids = [PurchaseCategory.objects.get(category=x).id for x in current_filter_list_unique] # To filter the Queryset below, we need to give a list of IDs to the category fields, as it's a foreign key
        print('Filters for chart: ' + str(current_filter_list_unique))


        queryset = Purchase.objects.filter(Q(category__in=current_filter_list_unique_ids) | Q(category_2__in=current_filter_list_unique_ids), date__gte=start_date_filter, date__lte=end_date_filter).values('date', 'amount').order_by('date')


        # DAILY CHART
        labels = []
        for datetime_index in pd.date_range(start_date_filter, end_date_filter, freq='D'): # freq='D' is default; returns a DateTime index
            labels.append(str(datetime_index.date()) + '  (' + calendar.day_name[datetime_index.weekday()][:2] + ')')

        values = []
        for date in labels:
            date = date[:-6] # Remove the prefix we just added so we can filter with the date
            amount_sum = 0 if queryset.filter(category__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount'))['amount__sum']
            amount_2_sum = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, date=date).aggregate(Sum('amount_2'))['amount_2__sum']
            values.append(amount_sum + amount_2_sum)


        # WEEKLY CHART
        dates_list = pd.date_range(start=start_date_filter, end=end_date_filter, freq='7D').strftime('%Y-%m-%d').tolist() # This will be a DateTimeIndex. Last two methods format the dates and turn into a list
        if dates_list[-1] != str(end_date_filter):
            dates_list.append(str(end_date_filter)) # Ensure we get all data up to the end_date_filter, even if the interval leaves a remainder

        labels_weekly = []
        values_weekly = []

        for date in dates_list: # If the last date is greater than end_date_filter, change it to end_date_filter, add the label, and end loop
            end_date = str((datetime.datetime.strptime(date, '%Y-%m-%d').date()+datetime.timedelta(days=6)))
            if date == str(end_date_filter): # Prevent showing a range like '01-01 - 01-01'. Instead, just show one date
                labels_weekly.append(date)
                break
            if end_date >= str(end_date_filter):
                labels_weekly.append(date + ' - ' + str(end_date_filter))
                break

            labels_weekly.append(date + ' - ' + end_date)

        for date_range in labels_weekly:
            if ' - ' in date_range:
                start_date, end_date = date_range.split(' - ')
            else:
                start_date, end_date = (date_range, date_range)
            amount_sum = 0 if queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
            amount_2_sum = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum']
            values_weekly.append(amount_sum + amount_2_sum)

        labels_weekly = [x[5:10] + ' - ' + x[-5:] if ' - ' in x else x[5:] for x in labels_weekly] # Removing the year component, as the label is too long


        # MONTHLY CHART
        dates_list = [start_date_filter]
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

        print(dates_list)
        print(dates_list[-1])
        print(end_date_filter)

        for date in dates_list: # If the last date is greater than end_date_filter, change it to end_date_filter, add the label, and end loop
            end_date = date+relativedelta(months=+1)+relativedelta(days=-1)
            if date == end_date_filter:
                labels_monthly.append(str(date))
                break
            if end_date >= end_date_filter:
                end_date = end_date_filter
                labels_monthly.append(str(date) + ' - ' + str(end_date))
                break
            labels_monthly.append(str(date) + ' - ' + str(end_date))

        for date_range in labels_monthly:
            if ' - ' in date_range:
                start_date, end_date = date_range.split(' - ')
            else:
                start_date, end_date = (date_range, date_range)
            amount_sum = 0 if queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum'] is None else queryset.filter(category__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
            amount_2_sum = 0 if queryset.filter(category_2__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum'] is None else queryset.filter(category_2__in=current_filter_list_unique_ids, date__gte=start_date, date__lte=end_date).aggregate(Sum('amount_2'))['amount_2__sum']
            values_monthly.append(amount_sum + amount_2_sum)

        labels_monthly = [x[5:10] + ' - ' + x[-5:] if ' - ' in x else x[5:] for x in labels_monthly] # Removing the year component, as the label is too long


        return JsonResponse({'labels': labels, 'values': values, 'labels_weekly': labels_weekly, 'values_weekly': values_weekly, 'labels_monthly': labels_monthly, 'values_monthly': values_monthly})


@login_required
def delete_purchase(request):
    Purchase.objects.get(id=request.POST['id']).delete()
    print('\nDeleted Purchase: ' + str(request.POST['id']) + '\n')
    return HttpResponse()


@login_required
def homepage(request):

    # bill_information = {
    # 'Apple Music': [7, 'Apple Music', 5.64, 'Monthly fee for Apple Music subscription.'],
    # 'Cell phone plan': [13, 'Cell phone plan', 41.81, 'Monthly fee for cell phone plan with Public Mobile.'],
    # 'Car insurance': [15, 'Car insurance', 137.91, 'Monthly fee for car insurance with TD Meloche.'],
    # 'Rent': [1, 'Rent', 750.00, 'Monthly rent for apartment.'],
    # }

    if request.method == 'GET':
        context = {}

        if len(Filter.objects.all()) < 2:
            Filter.objects.create()

        filter_instance = Filter.objects.last()

        context['start_date'] = '' if filter_instance.start_date_filter is None else str(filter_instance.start_date_filter)
        context['end_date'] = '' if filter_instance.end_date_filter is None else str(filter_instance.end_date_filter)

        # PurchaseCategory.objects.filter(category='').delete()
        # instance = PurchaseCategory.objects.get(category='Gas')
        # print(instance)
        # for object in Purchase.objects.all():
        #     object.category_2 = None
        #     object.save()

        # Get all bill instances
        # apple_music_queryset = Bill.objects.filter(bill='Apple Music').order_by('-last_update_date') # Querysets can return zero items
        # cell_phone_plan_queryset = Bill.objects.filter(bill='Cell phone plan').order_by('-last_update_date')
        # car_insurance_queryset = Bill.objects.filter(bill='Car insurance').order_by('-last_update_date')
        # rent_queryset = Bill.objects.filter(bill='Rent').order_by('-last_update_date')
        # gym_membership_queryset = Bill.objects.filter(bill='Gym membership').order_by('-last_update_date')

        # def check_bill_payments(bill, queryset):
        #     # Will create a Purchase object if True, since the month will match in the second if-statement
        #     instance_created_flag = False
        #     # If an instance doesn't exist, create it
        #     if len(queryset) == 0:
        #         if bill != 'Gym membership':
        #             instance = Bill.objects.create(bill = bill, last_update_date = datetime.datetime(year, month, bill_information[bill][0]))
        #             instance_created_flag = True
        #         else: # Create gym membership Bill
        #             instance = Bill.objects.create(bill = bill, last_update_date = datetime.datetime(2020, 2, 14))
        #     else:
        #         instance = queryset[0] # instance is either a Queryset or a real instance. This ensures it always becomes the latter
        #     # Check if bills for the current month have been recorded
        #     if bill != 'Gym membership':
        #         if instance.last_update_date.month != month and day >= instance.last_update_date.day:# or instance_created_flag is True:
        #             instance.last_update_date = datetime.datetime(year, month, bill_information[bill][0]) # Update the date. Won't matter if instance was just created
        #             instance.save()
        #
        #             Purchase.objects.create(date = datetime.datetime(year, month, bill_information[bill][0]),
        #                                     time = '00:00',
        #                                     amount = bill_information[bill][2],
        #                                     category = 'Bills',
        #                                     category_2 = '', # Worked without this line, but being safe
        #                                     item = bill,
        #                                     description = bill_information[bill][3] )
        #     else:
        #         if (((date + relativedelta(weekday=FR(-1))) - instance.last_update_date).days)%14 == 0 and (date - instance.last_update_date).days >=14:
        #             instance.last_update_date = date + relativedelta(weekday=FR(-1))
        #             instance.save()
        #
        #             Purchase.objects.create(date = date + relativedelta(weekday=FR(-1)),
        #                                     time = '00:00',
        #                                     amount = 10.16,
        #                                     category = 'Bills',
        #                                     category_2 = '', # Worked without this line, but being safe
        #                                     item = 'Gym membership',
        #                                     description = 'Bi-weekly fee.' )

        # check_bill_payments('Apple Music', apple_music_queryset)
        # check_bill_payments('Cell phone plan', cell_phone_plan_queryset)
        # check_bill_payments('Car insurance', car_insurance_queryset)
        # check_bill_payments('Rent', rent_queryset)
        # check_bill_payments('Gym membership', gym_membership_queryset)

    elif request.method == 'POST':

        purchase_form = PurchaseForm(request.POST, request.FILES)
        # print(purchase_form.errors)
        # print(request.FILES)
        purchase_instance = Purchase()

        if purchase_form.is_valid():
            purchase_instance.date = purchase_form.cleaned_data['date']
            purchase_instance.time = purchase_form.cleaned_data['time'] # Cleaning done in forms.py
            purchase_instance.item = purchase_form.cleaned_data['item'].strip()
            purchase_instance.category = purchase_form.cleaned_data['category']
            purchase_instance.amount = purchase_form.cleaned_data['amount']
            purchase_instance.category_2 = purchase_form.cleaned_data['category_2']
            purchase_instance.amount_2 = purchase_form.cleaned_data['amount_2']
            purchase_instance.description = purchase_form.cleaned_data['description'].strip() if len(purchase_form.cleaned_data['description'].strip()) == 0 or purchase_form.cleaned_data['description'].strip()[-1] == '.' else purchase_form.cleaned_data['description'].strip() + '.' # Add a period if not present
            purchase_instance.currency = purchase_form.cleaned_data['currency']
            purchase_instance.exchange_rate = get_exchange_rate(purchase_form.cleaned_data['currency'], 'CAD')
            purchase_instance.receipt = None if len(request.FILES) == 0 else request.FILES['receipt']

            purchase_instance.save()


            # Deal with the 2nd amount, which may be None
            amount_2 = 0
            if purchase_instance.amount_2 is not None:
                amount_2 = purchase_instance.amount_2

            # Increment the credit card balance only if indicated...
            if purchase_form.cleaned_data['disable_credit_card']: # Comes through as True or False
                # Get the latest debit account balance and create new AccountUpdate object with the balance decremented by the current purchase value
                debit_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=1)).order_by('-timestamp').first().value
                AccountUpdate.objects.create(account=Account.objects.get(id=1), value=debit_balance - purchase_instance.amount - amount_2, exchange_rate=purchase_instance.exchange_rate)
            else:
                # Get the latest credit card balance and create new AccountUpdate object with the balance incremented by the current purchase value
                credit_card_balance = AccountUpdate.objects.filter(account=Account.objects.get(id=3)).order_by('-timestamp').first().value
                AccountUpdate.objects.create(account=Account.objects.get(id=3), value=credit_card_balance + purchase_instance.amount + amount_2, exchange_rate=purchase_instance.exchange_rate)

            return redirect('homepage')
#
#         # ALERTS
#         mode_instance = Mode.objects.last()
#
#         if mode_instance is None:
#             mode_instance = Mode.objects.create( mode='All' )
#
#         if mode_instance.mode == 'All':
#             total_spent_to_date_coffee = Purchase.objects.filter((Q(category='Coffee') | Q(category_2='Coffee')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_groceries = Purchase.objects.filter((Q(category='Groceries') | Q(category_2='Groceries')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_food_drinks = Purchase.objects.filter((Q(category='Food/Drinks') | Q(category_2='Food/Drinks')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_restaurants = Purchase.objects.filter((Q(category='Restaurants') | Q(category_2='Restaurants')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_gas = Purchase.objects.filter((Q(category='Gas') | Q(category_2='Gas')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_dates = Purchase.objects.filter((Q(category='Dates') | Q(category_2='Dates')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#             total_spent_to_date_household_supplies = Purchase.objects.filter((Q(category='Household Supplies') | Q(category_2='Household Supplies')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#
#             a = total_spent_to_date_coffee['amount__sum']
#             b = total_spent_to_date_groceries['amount__sum']
#             c = total_spent_to_date_food_drinks['amount__sum']
#             d = total_spent_to_date_restaurants['amount__sum']
#             e = total_spent_to_date_gas['amount__sum']
#             f = total_spent_to_date_dates['amount__sum']
#             g = total_spent_to_date_household_supplies['amount__sum']
#             # If no money has been spent in a category, it will be None. This converts it to 0 if so
#             def check_none(variable):
#                 if variable is None:
#                     return 0
#                 else:
#                     return variable
#
#             a = check_none(a); b = check_none(b); c = check_none(c); d = check_none(d); e = check_none(e); f = check_none(f); g = check_none(g)
#
#             coffee_maximum = 20
#             groceries_maximum = 150
#             food_drinks_maximum = 50
#             restaurants_maximum = 100
#             gas_maximum = 75
#             dates_maximum = 100
#             household_supplies_maximum = 30
#
#             email_body = """\
# <html>
# <head></head>
# <body style="border-radius: 20px; padding: 1rem; color: black; font-size: 0.80rem; background-color: #d5e9fb">
# <u><h3>Monthly Spending in {}:</h3></u>
# <p style="margin-bottom: 0px; font-family: monospace; color: black"><b>Coffee</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Groceries</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Food/Drinks</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Restaurants</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Gas</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Dates</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# <p style="margin-top: 0px; font-family: monospace; color: black"><b>Household Supplies</b>: <span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
# </body>
# </html>
# """.format(month_name,
#            a, coffee_maximum, round((a/coffee_maximum)*100, 1),
#            b, groceries_maximum, round((b/groceries_maximum)*100, 1),
#            c, food_drinks_maximum, round((c/food_drinks_maximum)*100, 1),
#            d, restaurants_maximum, round((d/restaurants_maximum)*100, 1),
#            e, gas_maximum, round((e/gas_maximum)*100, 1),
#            f, dates_maximum, round((f/dates_maximum)*100, 1),
#            g, household_supplies_maximum, round((g/household_supplies_maximum)*100, 1) )
#
#             email_message = EmailMessage('Spending Alert', email_body, from_email='Spending Helper <spendinghelper@gmail.com>', to=['brendandagys@gmail.com'])
#             email_message.content_subtype = 'html'
#             email_message.send()
#
#         elif mode_instance.mode == 'Threshold':
#
#             def check_spending(category, maximum):
#                 # Get all purchases of the specific type for the current month
#                 alert_queryset = Alert.objects.filter(type=category, date_sent__gte=datetime.datetime(year, month, 1))
#                 # If no alerts have been created, make one
#                 if len(alert_queryset) == 0:
#                     instance = Alert.objects.create( type=category,
#                                                      percent=0,
#                                                      date_sent=datetime.datetime(year, month, 1) )
#                 # Otherwise take the first alert received (there will only be one...four in total)
#                 else:
#                     instance = alert_queryset[0]
#                     # Check if a new month has begun, and reset if so
#                     if month != instance.date_sent.month:
#                         instance.date_sent.month = month
#                         instance.percent = 0
#
#                 highest_threshold_reached = instance.percent
#
#                 # Get total spent this month on the specific type
#                 total_spent_to_date = Purchase.objects.filter((Q(category=category) | Q(category_2=category)) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
#                 total_spent_to_date = total_spent_to_date['amount__sum']
#
#                 send_email = True
#
#                 if total_spent_to_date is None:
#                     total_spent_to_date = 0
#
#                 if total_spent_to_date >= maximum:
#                     instance.percent = 100
#                     if highest_threshold_reached == 100:
#                         send_email = False
#
#                 elif total_spent_to_date >= floor(maximum * 0.75):
#                     instance.percent = 75
#                     if highest_threshold_reached >= 75:
#                         send_email = False
#
#                 elif total_spent_to_date >= floor(maximum * 0.5):
#                     instance.percent = 50
#                     if highest_threshold_reached >= 50:
#                         send_email = False
#
#                 elif total_spent_to_date >= floor(maximum * 0.25): # and (instance.percent < 25 or instance.percent in (50, 75, 100)):
#                     instance.percent = 25
#                     if highest_threshold_reached >= 25:
#                         send_email = False
#
#                 else:
#                     instance.percent = 0
#                     instance.save()
#                     return
#
#                 instance.save()
#
#                 if send_email is True:
#                     email_body = """\
# <html>
#   <head></head>
#   <body style="border-radius: 20px; padding: 1rem; color: black; font-size: 1.1rem; background-color: #d5e9fb">
#     <h3>You have reached {0}% of your monthly spending on {1}.</h3> </br>
#     <p>Spent in {2}: ${3}/${4}</p> </br>
#   </body>
# </html>
# """.format(round((total_spent_to_date/maximum)*100, 1), category, month_name, round(total_spent_to_date, 2), maximum)
#
#                     email_message = EmailMessage('Spending Alert for {0}'.format(category), email_body, from_email='Spending Helper <spendinghelper@gmail.com>', to=['brendandagys@gmail.com'])
#                     email_message.content_subtype = 'html'
#                     email_message.send()
#
#             # Run the function
#             check_spending('Coffee', 20)
#             check_spending('Groceries', 150)
#             check_spending('Food/Drinks', 50)
#             check_spending('Dates', 100)
#             check_spending('Restaurants', 100)
#             check_spending('Gas', 65)
#             check_spending('Household Supplies', 20)


    # This returns a blank form, (to clear for the next submission if request.method == 'POST')
    purchase_form = PurchaseForm()

    context['purchase_form'] = purchase_form
    context['purchase_categories_tuples_list'] = get_purchase_categories_tuples_list()

    return render(request, 'tracker/homepage.html', context=context)


class PurchaseListView(generic.ListView):
    # queryset = Purchase.objects.order_by('-date')
    # context_object_name = 'purchase_list'
    template_name = 'tracker/activity.html' # Specify your own template


    def get_queryset(self):
        # If none created yet, create an instance
        if len(Filter.objects.all()) < 2:
            Filter.objects.create()


    def get_context_data(self, *args, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(*args, **kwargs) # Simply using context = {} works, but being safe...

        # To generate fields for me to update account balances
        context['account_form'] = AccountForm()

        # To fill the datepickers with the current date filters and label the active filters
        filter_instance = Filter.objects.first()

        context['start_date'] = '' if filter_instance.start_date_filter is None else str(filter_instance.start_date_filter)
        context['end_date'] = '' if filter_instance.end_date_filter is None else str(filter_instance.end_date_filter)
        context['purchase_category_filters'] = [x.category for x in [filter_instance.category_filter_1, filter_instance.category_filter_2, filter_instance.category_filter_3, filter_instance.category_filter_4, filter_instance.category_filter_5,
                                                                     filter_instance.category_filter_6, filter_instance.category_filter_7, filter_instance.category_filter_8, filter_instance.category_filter_9, filter_instance.category_filter_10,
                                                                     filter_instance.category_filter_11, filter_instance.category_filter_12, filter_instance.category_filter_13, filter_instance.category_filter_14, filter_instance.category_filter_15,
                                                                     filter_instance.category_filter_16, filter_instance.category_filter_17, filter_instance.category_filter_18, filter_instance.category_filter_19, filter_instance.category_filter_20,
                                                                     filter_instance.category_filter_21, filter_instance.category_filter_22, filter_instance.category_filter_23, filter_instance.category_filter_24, filter_instance.category_filter_25]
                                                                     if x is not None]

        context['purchase_categories_tuples_list'] = get_purchase_categories_tuples_list()

        return context


@login_required
def settings(request):
    if request.method == 'GET':
        context = {}

        ThresholdFormSet = modelformset_factory(PurchaseCategory,
                                                fields=('category', 'threshold', 'threshold_rolling_days'),
                                                widgets={'category': TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:180px;'}),
                                                         'threshold': NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:95px;', 'inputmode': 'decimal'}),
                                                         'threshold_rolling_days': NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:53px;', 'inputmode': 'numeric'})})

        AccountFormSet = modelformset_factory(Account,
                                              exclude=(),
                                              widgets={'account': TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:200px;'}),
                                                       'credit': CheckboxInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:15px; margin:auto;'}),
                                                       'currency': Select(attrs={'class': 'form-control form-control-sm', 'style': 'width:67px; margin:auto;'}),
                                                       'active': CheckboxInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:15px; margin:auto;'})})

        context['threshold_formset'] = ThresholdFormSet()
        context['account_formset'] = AccountFormSet()

        context['recurring_list'] = Recurring.objects.all()
        context['recurring_form'] = RecurringForm()

        return render(request, 'tracker/settings.html', context=context)


@login_required
def filter_manager(request):

    if request.method == 'GET' and request.GET['page'] == 'Purchases' or request.method == 'POST' and request.POST['page'] == 'Purchases': # GET must be first!
        filter_instance = Filter.objects.first()
    else:
        filter_instance = Filter.objects.last()

    if request.method == 'POST' and request.POST['type'] != 'Date' or request.method == 'GET':
        # Generate a comprehensive list of PurchaseCategories
        full_category_filter_list = []
        for purchase_category in PurchaseCategory.objects.all():
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

    if request.method == 'GET':
        if len(current_filter_list_unique) == len(full_category_filter_list):
            current_filter_list_unique.append('All Categories')
        return JsonResponse(current_filter_list_unique, safe=False)

    if request.method == 'POST':
        # Get the filter that was clicked
        filter_value = request.POST['id'] # The filter 'value' is simply stored in the ID
        print('Clicked filter value: ' + str(filter_value))

        if request.POST['type'] == 'Date':
            filter_value = request.POST['filter_value']

            if filter_value == '':
                filter_value = None

            if request.POST['id'] == 'datepicker':
                filter_instance.start_date_filter = filter_value
            elif request.POST['id'] == 'datepicker_2':
                filter_instance.end_date_filter = filter_value

            filter_instance.save()

            return HttpResponse()

        elif request.POST['type'] == 'Category':

            def set_filters(filter_list):
                reset_filters()

                try:
                    filter_instance.category_filter_1 = None if filter_list[0] is None else PurchaseCategory.objects.get(category=filter_list[0])
                    filter_instance.category_filter_2 = None if filter_list[1] is None else PurchaseCategory.objects.get(category=filter_list[1])
                    filter_instance.category_filter_3 = None if filter_list[2] is None else PurchaseCategory.objects.get(category=filter_list[2])
                    filter_instance.category_filter_4 = None if filter_list[3] is None else PurchaseCategory.objects.get(category=filter_list[3])
                    filter_instance.category_filter_5 = None if filter_list[4] is None else PurchaseCategory.objects.get(category=filter_list[4])
                    filter_instance.category_filter_6 = None if filter_list[5] is None else PurchaseCategory.objects.get(category=filter_list[5])
                    filter_instance.category_filter_7 = None if filter_list[6] is None else PurchaseCategory.objects.get(category=filter_list[6])
                    filter_instance.category_filter_8 = None if filter_list[7] is None else PurchaseCategory.objects.get(category=filter_list[7])
                    filter_instance.category_filter_9 = None if filter_list[8] is None else PurchaseCategory.objects.get(category=filter_list[8])
                    filter_instance.category_filter_10 = None if filter_list[9] is None else PurchaseCategory.objects.get(category=filter_list[9])
                    filter_instance.category_filter_11 = None if filter_list[10] is None else PurchaseCategory.objects.get(category=filter_list[10])
                    filter_instance.category_filter_12 = None if filter_list[11] is None else PurchaseCategory.objects.get(category=filter_list[11])
                    filter_instance.category_filter_13 = None if filter_list[12] is None else PurchaseCategory.objects.get(category=filter_list[12])
                    filter_instance.category_filter_14 = None if filter_list[13] is None else PurchaseCategory.objects.get(category=filter_list[13])
                    filter_instance.category_filter_15 = None if filter_list[14] is None else PurchaseCategory.objects.get(category=filter_list[14])
                    filter_instance.category_filter_16 = None if filter_list[15] is None else PurchaseCategory.objects.get(category=filter_list[15])
                    filter_instance.category_filter_17 = None if filter_list[16] is None else PurchaseCategory.objects.get(category=filter_list[16])
                    filter_instance.category_filter_18 = None if filter_list[17] is None else PurchaseCategory.objects.get(category=filter_list[17])
                    filter_instance.category_filter_19 = None if filter_list[18] is None else PurchaseCategory.objects.get(category=filter_list[18])
                    filter_instance.category_filter_20 = None if filter_list[19] is None else PurchaseCategory.objects.get(category=filter_list[19])
                    filter_instance.category_filter_21 = None if filter_list[20] is None else PurchaseCategory.objects.get(category=filter_list[20])
                    filter_instance.category_filter_22 = None if filter_list[21] is None else PurchaseCategory.objects.get(category=filter_list[21])
                    filter_instance.category_filter_23 = None if filter_list[22] is None else PurchaseCategory.objects.get(category=filter_list[22])
                    filter_instance.category_filter_24 = None if filter_list[23] is None else PurchaseCategory.objects.get(category=filter_list[23])
                    filter_instance.category_filter_25 = None if filter_list[24] is None else PurchaseCategory.objects.get(category=filter_list[24])
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
                if len(current_filter_list_unique) == len(full_category_filter_list):
                    return JsonResponse([], safe=False) # safe=False necessary for non-dict objects to be serialized
                else:
                    set_filters(full_category_filter_list)
                    full_category_filter_list.append('All Categories')
                    return JsonResponse(full_category_filter_list, safe=False) # safe=False necessary for non-dict objets to be serialized

            else:
                if len(current_filter_list_unique) == 25: # Otherwise, there's an available slot...
                    reset_filters()
                    return JsonResponse([], safe=False) # safe=False necessary for non-dict objects to be serialized

                else:
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
def mode_manager(request):
    if request.method == 'GET':
        mode_instance = Mode.objects.last()

        if mode_instance is None:
            mode_instance = Mode.objects.create(mode='All')

        return JsonResponse( {'mode': mode_instance.mode} )

    elif request.method == 'POST':
        mode_instance = Mode.objects.last()
        mode_instance.mode = request.POST['mode']
        mode_instance.save()

        return HttpResponse()
