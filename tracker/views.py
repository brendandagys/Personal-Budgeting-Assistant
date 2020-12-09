from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage

from django.db.models import Q

# from django.contrib.auth.mixins import LoginRequiredMixin # Done in urls.py
from django.contrib.auth.decorators import login_required

from django.views import generic
from .forms import PurchaseForm, AccountForm
from .models import Purchase, Filter, Bill, Alert, Mode, PurchaseCategory

from django.db.models import Sum

from math import floor
import datetime
import calendar
from dateutil.relativedelta import *
import re
import pandas as pd

# Get information about today's date
date = datetime.date.today()
year = date.year
month = date.month
month_name = calendar.month_name[date.month]
day = date.day
weekday = date.weekday()

@login_required # Don't think this is necessary
def get_chart_data(request):

    if request.method == 'GET':
        category = request.GET['category']
        if request.GET['filter'] == 'Wee': # I slice 2 - 5 in the JavaScript, so only three characters are sent
            days_filter = 'Weeks'
        else:
            days_filter = int(request.GET['filter']) - 1 # Comes through as '025' or '050' or '100' | gives one extra, so subtract

        # To send to the front-end
        json = dict()

        # List comprehension wouldn't work unless these were created first
        labels = []
        values = []

        if days_filter != 'Weeks':

            # if category == 'All': # Don't add category filter to the query
            #     queryset = Purchase.objects.filter(date__gte=date - datetime.timedelta(days=days_filter)).values('date', 'amount').order_by('date')
            # else:
            #     queryset = Purchase.objects.filter(Q(date__gte=date - datetime.timedelta(days=days_filter)) & (Q(category=category) | Q(category_2=category))).values('date', 'amount').order_by('date')

            # Range from 100 to 0
            for x in range(days_filter, -1, -1):
                labels.append(str(date-datetime.timedelta(days=x)))

            for x in labels:
                if category == 'All':
                    queryset = Purchase.objects.filter(date=x).exclude(category='Bills').values('amount').aggregate(Sum('amount'))
                else:
                    queryset = Purchase.objects.filter(Q(date=x) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount')) # Get all purchase amounts on that date

                if queryset['amount__sum'] is None:
                    values.append(0)
                else:
                    values.append(queryset['amount__sum'])

            # print(values)

        elif days_filter == 'Weeks':

            week_1_begin  = date + relativedelta(weeks=-11, weekday=SU(-1))
            week_1_end    = date + relativedelta(weeks=-11, weekday=SA(1))
            week_2_begin  = date + relativedelta(weeks=-10, weekday=SU(-1))
            week_2_end    = date + relativedelta(weeks=-10, weekday=SA(1))
            week_3_begin  = date + relativedelta(weeks=-9, weekday=SU(-1))
            week_3_end    = date + relativedelta(weeks=-9, weekday=SA(1))
            week_4_begin  = date + relativedelta(weeks=-8, weekday=SU(-1))
            week_4_end    = date + relativedelta(weeks=-8, weekday=SA(1))
            week_5_begin  = date + relativedelta(weeks=-7, weekday=SU(-1))
            week_5_end    = date + relativedelta(weeks=-7, weekday=SA(1))
            week_6_begin  = date + relativedelta(weeks=-6, weekday=SU(-1))
            week_6_end    = date + relativedelta(weeks=-6, weekday=SA(1))
            week_7_begin  = date + relativedelta(weeks=-5, weekday=SU(-1))
            week_7_end    = date + relativedelta(weeks=-5, weekday=SA(1))
            week_8_begin  = date + relativedelta(weeks=-4, weekday=SU(-1))
            week_8_end    = date + relativedelta(weeks=-4, weekday=SA(1))
            week_9_begin  = date + relativedelta(weeks=-3, weekday=SU(-1))
            week_9_end    = date + relativedelta(weeks=-3, weekday=SA(1))
            week_10_begin = date + relativedelta(weeks=-2, weekday=SU(-1))
            week_10_end   = date + relativedelta(weeks=-2, weekday=SA(1))
            week_11_begin = date + relativedelta(weeks=-1, weekday=SU(-1))
            week_11_end   = date + relativedelta(weeks=-1, weekday=SA(1))
            week_12_begin = date + relativedelta(weekday=SU(-1))
            week_12_end   = date + relativedelta(weekday=SA(1))

            if category == 'All': # Don't add category filter to the query
                queryset_week_1  = Purchase.objects.filter(date__gte = week_1_begin, date__lte = week_1_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_2  = Purchase.objects.filter(date__gte = week_2_begin, date__lte = week_2_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_3  = Purchase.objects.filter(date__gte = week_3_begin, date__lte = week_3_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_4  = Purchase.objects.filter(date__gte = week_4_begin, date__lte = week_4_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_5  = Purchase.objects.filter(date__gte = week_5_begin, date__lte = week_5_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_6  = Purchase.objects.filter(date__gte = week_6_begin, date__lte = week_6_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_7  = Purchase.objects.filter(date__gte = week_7_begin, date__lte = week_7_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_8  = Purchase.objects.filter(date__gte = week_8_begin, date__lte = week_8_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_9  = Purchase.objects.filter(date__gte = week_9_begin, date__lte = week_9_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_10 = Purchase.objects.filter(date__gte = week_10_begin, date__lte = week_10_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_11 = Purchase.objects.filter(date__gte = week_11_begin, date__lte = week_11_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
                queryset_week_12 = Purchase.objects.filter(date__gte = week_12_begin, date__lte = week_12_end).exclude(Q(category='Bills') | Q(category_2='Bills')).values('amount').aggregate(Sum('amount'))
            else:
                queryset_week_1  = Purchase.objects.filter(Q(date__gte = week_1_begin) & Q(date__lte = week_1_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_2  = Purchase.objects.filter(Q(date__gte = week_2_begin) & Q(date__lte = week_2_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_3  = Purchase.objects.filter(Q(date__gte = week_3_begin) & Q(date__lte = week_3_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_4  = Purchase.objects.filter(Q(date__gte = week_4_begin) & Q(date__lte = week_4_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_5  = Purchase.objects.filter(Q(date__gte = week_5_begin) & Q(date__lte = week_5_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_6  = Purchase.objects.filter(Q(date__gte = week_6_begin) & Q(date__lte = week_6_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_7  = Purchase.objects.filter(Q(date__gte = week_7_begin) & Q(date__lte = week_7_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_8  = Purchase.objects.filter(Q(date__gte = week_8_begin) & Q(date__lte = week_8_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_9  = Purchase.objects.filter(Q(date__gte = week_9_begin) & Q(date__lte = week_9_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_10  = Purchase.objects.filter(Q(date__gte = week_10_begin) & Q(date__lte = week_10_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_11  = Purchase.objects.filter(Q(date__gte = week_11_begin) & Q(date__lte = week_11_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))
                queryset_week_12  = Purchase.objects.filter(Q(date__gte = week_12_begin) & Q(date__lte = week_12_end) & (Q(category=category) | Q(category_2=category))).values('amount').aggregate(Sum('amount'))

            labels = [' - '.join([str(week_1_begin)[5:10], str(week_1_end)[5:10]]),
                      ' - '.join([str(week_2_begin)[5:10], str(week_2_end)[5:10]]),
                      ' - '.join([str(week_3_begin)[5:10], str(week_3_end)[5:10]]),
                      ' - '.join([str(week_4_begin)[5:10], str(week_4_end)[5:10]]),
                      ' - '.join([str(week_5_begin)[5:10], str(week_5_end)[5:10]]),
                      ' - '.join([str(week_6_begin)[5:10], str(week_6_end)[5:10]]),
                      ' - '.join([str(week_7_begin)[5:10], str(week_7_end)[5:10]]),
                      ' - '.join([str(week_8_begin)[5:10], str(week_8_end)[5:10]]),
                      ' - '.join([str(week_9_begin)[5:10], str(week_9_end)[5:10]]),
                      ' - '.join([str(week_10_begin)[5:10], str(week_10_end)[5:10]]),
                      ' - '.join([str(week_11_begin)[5:10], str(week_11_end)[5:10]]),
                      ' - '.join([str(week_12_begin)[5:10], str(week_12_end)[5:10]]) ]

            for set in [queryset_week_1, queryset_week_2, queryset_week_3, queryset_week_4, queryset_week_5, queryset_week_6, queryset_week_7, queryset_week_8, queryset_week_9, queryset_week_10, queryset_week_11, queryset_week_12]:
                if set['amount__sum'] is None:
                    values.append(0)
                else:
                    values.append(set['amount__sum'])

        json[category] = {'labels': labels, 'values': values}

        # print(json)

        return JsonResponse(json)

@login_required
def homepage(request):

    # bill_information = {
    # 'Apple Music': [7, 'Apple Music', 5.64, 'Monthly fee for Apple Music subscription.'],
    # 'Cell phone plan': [13, 'Cell phone plan', 41.81, 'Monthly fee for cell phone plan with Public Mobile.'],
    # 'Car insurance': [15, 'Car insurance', 137.91, 'Monthly fee for car insurance with TD Meloche.'],
    # 'Rent': [1, 'Rent', 750.00, 'Monthly rent for apartment.'],
    # }

    if request.method == 'GET':
        pass
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

        purchase_form = PurchaseForm(request.POST)
        # print(purchase_form.errors)
        purchase_instance = Purchase()

        if purchase_form.is_valid():

            purchase_instance.date = purchase_form.cleaned_data['date']
            purchase_instance.time = purchase_form.cleaned_data['time'].strip()
            purchase_instance.item = purchase_form.cleaned_data['item'].strip()
            purchase_instance.category = purchase_form.cleaned_data['category'].strip()
            purchase_instance.amount = purchase_form.cleaned_data['amount']
            purchase_instance.category_2 = purchase_form.cleaned_data['category_2'].strip()
            purchase_instance.amount_2 = purchase_form.cleaned_data['amount_2']
            purchase_instance.description = purchase_form.cleaned_data['description'].strip()

            # Clean time fields
            time = purchase_instance.time

            if len(time) == 0:
                time = '00:00'

            elif len(time) == 1:
                if time in [str(x) for x in range(10)]:
                    time = '0' + time + ':00'
                else:
                    time = '00:00'

            elif time [0:2] in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
                                '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
                if len(time) == 5 and time[2] == ':' and int(time[3]) in range(6) and int(time[4]) in range(10):
                    pass
                elif len(time) == 4 and int(time[2]) in range(6) and int(time[3]) in range(10):
                    time = time[0:2] + ':' + time[2:4]
                else:
                    time = time[0:2] + ':00'

            elif time[0] in [str(x) for x in range(10)] and time[1] == ':':
                if len(time) == 4 and int(time[2]) in range(6) and int(time[3]) in range(10):
                    time = '0' + time
                else:
                    time = '0' + time[0] + ':00'

            else:
                time = '00:00'

            purchase_instance.time = time
            purchase_instance.save()

        # ALERTS
        mode_instance = Mode.objects.last()

        if mode_instance is None:
            mode_instance = Mode.objects.create( mode='All' )

        if mode_instance.mode == 'All':
            total_spent_to_date_coffee = Purchase.objects.filter((Q(category='Coffee') | Q(category_2='Coffee')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_groceries = Purchase.objects.filter((Q(category='Groceries') | Q(category_2='Groceries')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_food_drinks = Purchase.objects.filter((Q(category='Food/Drinks') | Q(category_2='Food/Drinks')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_restaurants = Purchase.objects.filter((Q(category='Restaurants') | Q(category_2='Restaurants')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_gas = Purchase.objects.filter((Q(category='Gas') | Q(category_2='Gas')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_dates = Purchase.objects.filter((Q(category='Dates') | Q(category_2='Dates')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
            total_spent_to_date_household_supplies = Purchase.objects.filter((Q(category='Household Supplies') | Q(category_2='Household Supplies')) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))

            a = total_spent_to_date_coffee['amount__sum']
            b = total_spent_to_date_groceries['amount__sum']
            c = total_spent_to_date_food_drinks['amount__sum']
            d = total_spent_to_date_restaurants['amount__sum']
            e = total_spent_to_date_gas['amount__sum']
            f = total_spent_to_date_dates['amount__sum']
            g = total_spent_to_date_household_supplies['amount__sum']
            # If no money has been spent in a category, it will be None. This converts it to 0 if so
            def check_none(variable):
                if variable is None:
                    return 0
                else:
                    return variable

            a = check_none(a); b = check_none(b); c = check_none(c); d = check_none(d); e = check_none(e); f = check_none(f); g = check_none(g)

            coffee_maximum = 20
            groceries_maximum = 150
            food_drinks_maximum = 50
            restaurants_maximum = 100
            gas_maximum = 75
            dates_maximum = 100
            household_supplies_maximum = 30

            email_body = """\
<html>
<head></head>
<body style="border-radius: 20px; padding: 1rem; color: black; font-size: 0.80rem; background-color: #d5e9fb">
<u><h3>Monthly Spending in {}:</h3></u>
<p style="margin-bottom: 0px; font-family: monospace; color: black"><b>Coffee</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Groceries</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Food/Drinks</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Restaurants</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Gas</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-bottom: 0px; margin-top: 0px; font-family: monospace; color: black"><b>Dates</b>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
<p style="margin-top: 0px; font-family: monospace; color: black"><b>Household Supplies</b>: <span style="display: inline-block; width: 70px;">${}/${}</span> - <b>({}%)</b></p> </br>
</body>
</html>
""".format(month_name,
           a, coffee_maximum, round((a/coffee_maximum)*100, 1),
           b, groceries_maximum, round((b/groceries_maximum)*100, 1),
           c, food_drinks_maximum, round((c/food_drinks_maximum)*100, 1),
           d, restaurants_maximum, round((d/restaurants_maximum)*100, 1),
           e, gas_maximum, round((e/gas_maximum)*100, 1),
           f, dates_maximum, round((f/dates_maximum)*100, 1),
           g, household_supplies_maximum, round((g/household_supplies_maximum)*100, 1) )

            email_message = EmailMessage('Spending Alert', email_body, from_email='Spending Helper <spendinghelper@gmail.com>', to=['brendandagys@gmail.com'])
            email_message.content_subtype = 'html'
            email_message.send()

        elif mode_instance.mode == 'Threshold':

            def check_spending(category, maximum):
                # Get all purchases of the specific type for the current month
                alert_queryset = Alert.objects.filter(type=category, date_sent__gte=datetime.datetime(year, month, 1))
                # If no alerts have been created, make one
                if len(alert_queryset) == 0:
                    instance = Alert.objects.create( type=category,
                                                     percent=0,
                                                     date_sent=datetime.datetime(year, month, 1) )
                # Otherwise take the first alert received (there will only be one...four in total)
                else:
                    instance = alert_queryset[0]
                    # Check if a new month has begun, and reset if so
                    if month != instance.date_sent.month:
                        instance.date_sent.month = month
                        instance.percent = 0

                highest_threshold_reached = instance.percent

                # Get total spent this month on the specific type
                total_spent_to_date = Purchase.objects.filter((Q(category=category) | Q(category_2=category)) & Q(date__gte=datetime.datetime(year, month, 1))).aggregate(Sum('amount'))
                total_spent_to_date = total_spent_to_date['amount__sum']

                send_email = True

                if total_spent_to_date is None:
                    total_spent_to_date = 0

                if total_spent_to_date >= maximum:
                    instance.percent = 100
                    if highest_threshold_reached == 100:
                        send_email = False

                elif total_spent_to_date >= floor(maximum * 0.75):
                    instance.percent = 75
                    if highest_threshold_reached >= 75:
                        send_email = False

                elif total_spent_to_date >= floor(maximum * 0.5):
                    instance.percent = 50
                    if highest_threshold_reached >= 50:
                        send_email = False

                elif total_spent_to_date >= floor(maximum * 0.25): # and (instance.percent < 25 or instance.percent in (50, 75, 100)):
                    instance.percent = 25
                    if highest_threshold_reached >= 25:
                        send_email = False

                else:
                    instance.percent = 0
                    instance.save()
                    return

                instance.save()

                if send_email is True:
                    email_body = """\
<html>
  <head></head>
  <body style="border-radius: 20px; padding: 1rem; color: black; font-size: 1.1rem; background-color: #d5e9fb">
    <h3>You have reached {0}% of your monthly spending on {1}.</h3> </br>
    <p>Spent in {2}: ${3}/${4}</p> </br>
  </body>
</html>
""".format(round((total_spent_to_date/maximum)*100, 1), category, month_name, round(total_spent_to_date, 2), maximum)

                    email_message = EmailMessage('Spending Alert for {0}'.format(category), email_body, from_email='Spending Helper <spendinghelper@gmail.com>', to=['brendandagys@gmail.com'])
                    email_message.content_subtype = 'html'
                    email_message.send()

            # Run the function
            check_spending('Coffee', 20)
            check_spending('Groceries', 150)
            check_spending('Food/Drinks', 50)
            check_spending('Dates', 100)
            check_spending('Restaurants', 100)
            check_spending('Gas', 65)
            check_spending('Household Supplies', 20)

    # This returns a blank form, (to clear for the next submission if request.method == 'POST')
    purchase_form = PurchaseForm()

    context = {'purchase_form': purchase_form}

    return render(request, 'homepage.html', context=context)


class PurchaseListView(generic.ListView):
    queryset = Purchase.objects.order_by('-date')
    context_object_name = 'purchase_list'
    template_name = 'tracker/transaction_list.html' # Specify your own template

    # def get_time_filter(self, parameter):

        # if parameter == 'Last Seven Days':
        #     return [date - datetime.timedelta(days=6), date]
        # elif parameter == 'Last 30 Days':
        #     return [date - datetime.timedelta(days=29), date]
        # elif parameter == 'Last Three Months':
        #     return [date + relativedelta(months=-3), date]
        # elif parameter == 'Last Six Months:':
        #     return [date + relativedelta(months=-6), date]
        # elif parameter == 'Last Year':
        #     return [date + relativedelta(years=-1), date]
        # elif parameter == 'This Week': # 0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday, 4 = Friday, 5 = Saturday, 6 = Sunday
        #     return [date - datetime.timedelta(days=1+weekday), date]
        # elif parameter == 'One Week Ago':
        #     return [date + relativedelta(weeks=-1, weekday=SU(-1)), date + relativedelta(weeks=-1, weekday=SA(1))]
        # elif parameter == 'Two Weeks Ago':
        #     return [date + relativedelta(weeks=-2, weekday=SU(-1)), date + relativedelta(weeks=-2, weekday=SA(1))]
        # elif parameter == 'Three Weeks Ago':
        #     return [date + relativedelta(weeks=-3, weekday=SU(-1)), date + relativedelta(weeks=-3, weekday=SA(1))]
        # elif parameter == 'Four Weeks Ago':
        #     return [date + relativedelta(weeks=-4, weekday=SU(-1)), date + relativedelta(weeks=-4, weekday=SA(1))]
        # elif parameter == 'This Month':
        #     return [datetime.datetime(year, month, 1).date(), date]
        # elif parameter == 'One Month Ago':
        #     return [date + relativedelta(day=1, months=-1), date + relativedelta(day=31, months=-1)]
        # elif parameter == 'Two Months Ago':
        #     return [date + relativedelta(day=1, months=-2), date + relativedelta(day=31, months=-2)]
        # elif parameter == 'Three Months Ago':
        #     return [date + relativedelta(day=1, months=-3), date + relativedelta(day=31, months=-3)]
        # elif parameter == 'Four Months Ago':
        #     return [date + relativedelta(day=1, months=-4), date + relativedelta(day=31, months=-4)]
        # elif parameter == 'This Year':
        #     return [datetime.datetime(year, 1, 1).date(), date]
        #
        # else:
        #     return [date - datetime.timedelta(days=5000), date]


    def get_queryset(self):

        filters_instance = Filter.objects.last() # Gives object or None
        # If no filter instance exists or five or more minutes have passed
        if filters_instance is None or (datetime.datetime.now() - datetime.datetime.strptime(filters_instance.last_update_time.split('.')[0], "%Y-%m-%d %H:%M:%S")).total_seconds()/60 >= 5:
            category_filter = ''
            time_filter_start = ''
            time_filter_end = ''
            deactivate_category = 'No'
            deactivate_time = 'No'

        else:
            category_filter = filters_instance.category_filter
            time_filter_start = self.get_time_filter(filters_instance.time_filter)[0]
            time_filter_end = self.get_time_filter(filters_instance.time_filter)[1]
            deactivate_category = filters_instance.deactivate_category
            deactivate_time = filters_instance.deactivate_time

        if deactivate_category == 'Yes':
            category_filter = ''
        if deactivate_time == 'Yes':
            time_filter_start = ''

        if category_filter == '' and time_filter_start != '':
            return Purchase.objects.filter(Q(date__gte=time_filter_start) & Q(date__lte=time_filter_end)).order_by('-date', '-time')

        elif category_filter != '' and time_filter_start == '':
            return Purchase.objects.filter(Q(category=category_filter) | Q(category_2=category_filter)).order_by('-date', '-time')

        elif category_filter != '' and time_filter_start != '':
            return Purchase.objects.filter(Q(date__gte=time_filter_start) & Q(date__lte=time_filter_end) & (Q(category=category_filter) | Q(category_2=category_filter))).order_by('-date', '-time')

        else:
            return Purchase.objects.all().order_by('-date', '-time')


    def get_context_data(self, *args, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(*args, **kwargs)

        context['account_form'] = AccountForm()

        return context


@login_required
def filter_manager(request):

    def get_time_filter(parameter):

        if parameter == 'Last Seven Days':
            return [date - datetime.timedelta(days=6), date]
        elif parameter == 'Last 30 Days':
            return [date - datetime.timedelta(days=29), date]
        elif parameter == 'Last Three Months':
            return [date + relativedelta(months=-3), date]
        elif parameter == 'Last Six Months:':
            return [date + relativedelta(months=-6), date]
        elif parameter == 'Last Year':
            return [date + relativedelta(years=-1), date]
        elif parameter == 'This Week': # 0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday, 4 = Friday, 5 = Saturday, 6 = Sunday
            return [date - datetime.timedelta(days=1+weekday), date]
        elif parameter == 'One Week Ago':
            return [date + relativedelta(weeks=-1, weekday=SU(-1)), date + relativedelta(weeks=-1, weekday=SA(1))]
        elif parameter == 'Two Weeks Ago':
            return [date + relativedelta(weeks=-2, weekday=SU(-1)), date + relativedelta(weeks=-2, weekday=SA(1))]
        elif parameter == 'Three Weeks Ago':
            return [date + relativedelta(weeks=-3, weekday=SU(-1)), date + relativedelta(weeks=-3, weekday=SA(1))]
        elif parameter == 'Four Weeks Ago':
            return [date + relativedelta(weeks=-4, weekday=SU(-1)), date + relativedelta(weeks=-4, weekday=SA(1))]
        elif parameter == 'This Month':
            return [datetime.datetime(year, month, 1).date(), date]
        elif parameter == 'One Month Ago':
            return [date + relativedelta(day=1, months=-1), date + relativedelta(day=31, months=-1)]
        elif parameter == 'Two Months Ago':
            return [date + relativedelta(day=1, months=-2), date + relativedelta(day=31, months=-2)]
        elif parameter == 'Three Months Ago':
            return [date + relativedelta(day=1, months=-3), date + relativedelta(day=31, months=-3)]
        elif parameter == 'Four Months Ago':
            return [date + relativedelta(day=1, months=-4), date + relativedelta(day=31, months=-4)]
        elif parameter == 'This Year':
            return [datetime.datetime(year, 1, 1).date(), date]

        else:
            return [datetime.datetime(2019, 12, 1).date(), date]

    if request.method == 'POST':

        filters_instance = Filter.objects.all()[0] # Gives object or raises an exception

        filters_instance.last_update_date = datetime.date.today()
        filters_instance.last_update_time = datetime.datetime.now()

        if request.POST['filter'][0] == 'c':
            if request.POST['filter'][1:] == filters_instance.category_filter:
                filters_instance.deactivate = 'Yes'
                filters_instance.category_filter = ''
            else:
                filters_instance.category_filter = request.POST['filter'][1:]

        elif request.POST['filter'][0] == 't':
            if request.POST['filter'][1:] == filters_instance.time_filter:
                filters_instance.deactivate = 'Yes'
                filters_instance.time_filter = ''
            else:
                filters_instance.time_filter = request.POST['filter'][1:]

        else: # 'NO FILTER' was selected
            filters_instance.category_filter = ''
            filters_instance.time_filter = ''

        filters_instance.save()

        return HttpResponse()

    # elif request.method == 'GET':
    #
    #     try:
    #         filters_instance = Filter.objects.all()[0]
    #
    #     except:
    #         filters_instance = Filter.objects.create(last_update_date = datetime.date.today(),
    #                                                  last_update_time = datetime.datetime.now(),
    #                                                  category_filter = '',
    #                                                  time_filter = '',
    #                                                  deactivate_category = 'No',
    #                                                  deactivate_time = 'No' )
    #
    #     # Return the sum of money spent for the given filters
    #
    #     if filters_instance.deactivate_category == 'Yes':
    #         category_filter = ''
    #     else:
    #         category_filter = filters_instance.category_filter
    #
    #     if filters_instance.deactivate_time == 'Yes':
    #         time_filter = ''
    #         time_filter_start = ''
    #         time_filter_end = ''
    #     else:
    #         time_filter = filters_instance.time_filter
    #         time_filter_start = get_time_filter(filters_instance.time_filter)[0]
    #         time_filter_end = get_time_filter(filters_instance.time_filter)[1]
    #
    #     if category_filter == '' and time_filter_start != '':
    #         purchase_instance = Purchase.objects.filter(Q(date__gte=time_filter_start) & Q(date__lte=time_filter_end)).order_by('-date', '-time')
    #
    #     elif category_filter != '' and time_filter_start == '':
    #         purchase_instance = Purchase.objects.filter(Q(category=category_filter) | Q(category_2=category_filter)).order_by('-date', '-time')
    #
    #     elif category_filter != '' and time_filter_start != '':
    #         purchase_instance = Purchase.objects.filter(Q(date__gte=time_filter_start) & Q(date__lte=time_filter_end) & (Q(category=category_filter) | Q(category_2=category_filter))).order_by('-date', '-time')
    #
    #     else:
    #         purchase_instance = Purchase.objects.all()
    #
    #     # If there are no objects, the sum will be None
    #     try:
    #         total_spent = '$' + str(round(purchase_instance.aggregate(Sum('amount'))['amount__sum'], 2))
    #     except:
    #         total_spent = '$0'
    #
    #     return JsonResponse({'category_filter': category_filter.replace(' ', '').replace('/', '').lower(),
    #                          'time_filter': time_filter.replace(' ', '').replace('/', '').lower(),
    #                          'time_filter_start': time_filter_start,
    #                          'time_filter_end': time_filter_end,
    #                          'total_spent': total_spent, })

    return HttpResponse()

@login_required
def manage_mode(request):
    if request.method == 'GET':
        mode_instance = Mode.objects.last()

        if mode_instance is None:
            mode_instance = Mode.objects.create( mode='All' )

        return JsonResponse( {'mode': mode_instance.mode} )

    elif request.method == 'POST':
        mode_instance = Mode.objects.last()
        mode_instance.mode = request.POST['mode']
        mode_instance.save()

        return HttpResponse()
