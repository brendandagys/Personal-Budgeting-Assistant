from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.views import generic
from .forms import PurchaseForm
from .models import Purchase, Filter, Bill

from django.db.models import Sum

import datetime
import re

@login_required
def homepage(request):

    bill_information = {
    'Apple Music': [7, 'Apple Music', 5.64, 'Monthly fee for Apple Music subscription.'],
    'Cell phone plan': [13, 'Cell phone plan', 41.81, 'Monthly fee for cell phone plan with Public Mobile.'],
    'Car insurance': [15, 'Car insurance', 137.91, 'Monthly fee for car insurance with TD Meloche.'],
    'Rent': [1, 'Rent', 750.00, 'Monthly rent for apartment.'],
    }

    # Get information about today's date
    date = datetime.date.today()
    year = date.year
    month = date.month
    day = date.day

    if request.method == 'GET':

        # Get all bill instances
        apple_music_queryset = Bill.objects.filter(bill='Apple Music').order_by('-last_update_date') # Querysets can return zero items
        cell_phone_queryset = Bill.objects.filter(bill='Cell phone').order_by('-last_update_date')
        car_insurance_queryset = Bill.objects.filter(bill='Car insurance').order_by('-last_update_date')
        rent_queryset = Bill.objects.filter(bill='Rent').order_by('-last_update_date')

        def check_bill_payments(bill, queryset):
            # Will create a Purchase object if True, since the month will match in the second if-statement
            instance_created_flag = False
            # If an instance doesn't exist, create it
            if len(queryset) == 0:
                instance = Bill.objects.create(bill = bill, last_update_date = datetime.datetime(year, month, bill_information[bill][0]))
                instance_created_flag = True
            else:
                instance = queryset[0] # instance is either a Queryset or a real instance. This ensures it always becomes the latter
            # Check if bills for the current month have been recorded
            if (instance.last_update_date.month != month and day > instance.last_update_date.day) or instance_created_flag is True:
                instance.last_update_date = datetime.datetime(year, month, bill_information[bill][0]) # Update the date. Won't matter if instance was just created

                Purchase.objects.create(date = datetime.datetime(year, month, bill_information[bill][0]),
                                        time = '00:00',
                                        amount = bill_information[bill][2],
                                        category = 'Bills',
                                        item = bill,
                                        description = bill_information[bill][3] )

        check_bill_payments('Apple Music', apple_music_queryset)
        check_bill_payments('Cell phone plan', cell_phone_queryset)
        check_bill_payments('Car insurance', car_insurance_queryset)
        check_bill_payments('Rent', rent_queryset)

    elif request.method == 'POST':

        purchase_form = PurchaseForm(request.POST)
        # print(purchase_form.errors)
        purchase_instance = Purchase()

        if purchase_form.is_valid():

            purchase_instance.date = purchase_form.cleaned_data['date']
            purchase_instance.time = purchase_form.cleaned_data['time'].strip()
            purchase_instance.amount = purchase_form.cleaned_data['amount']
            purchase_instance.category = purchase_form.cleaned_data['category'].strip()
            purchase_instance.item = purchase_form.cleaned_data['item'].strip()
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


    def check_spending(item, maximum):
        total_spent_to_date = Purchase.objects.filter(item=item, date__gte=datetime.datetime(year, month, 1)).aggregate(Sum('amount'))
        print(total_spent_to_date)
        if total_spent_to_date >= maximum:
            notification = '100%'
        elif total_spent_to_date >= floor(maximum * 0.75):
            notification = '75%'
        elif total_spent_to_date >= floor(maximum * 0.5):
            notification = '50%'
        elif total_spent_to_date >= floor(maximum * 0.25):
            notification = '25%'

        email_body = """\
<html>
  <head></head>
  <body style="border-radius: 20px; padding: 1rem; color: black; font-size: 1.1rem; background-color: #d5e9fb">
    <h3>You have reached {0} of your monthly spending on {1}.</h3> </br>
    <p>Spent this month: ${2}/${3}</p> </br>
  </body>
</html>
""".format(notification, item, total_spent_to_date, maximum)

        email_message = EmailMessage('Spending Alert for {0}'.format(item), email_body, from_email='Spending Helper <spendinghelper@gmail.com', to=['brendandagys@gmail.com'])
        email_message.content_subtype = 'html'
        email_message.send()

        send_email()
    # Run the function
    check_spending('Coffee', 20)
    check_spending('Groceries', 100)
    check_spending('Food/Drinks', 50)
    check_spending('Dates', 100)

    # This returns a blank form, (to clear for the next submission if request.method == 'POST')
    purchase_form = PurchaseForm()

    context = {'purchase_form': purchase_form}

    return render(request, 'homepage.html', context=context)


class PurchaseListView(generic.ListView):
    context_object_name = 'purchase_list'
    # queryset = Purchase.objects.order_by('-date')
    template_name = 'tracker/transaction_list.html' # Specify your own template

    def get_time_filter(self, parameter):

        if parameter == 'Last Week':
            return datetime.date.today() - datetime.timedelta(days=7)
        elif parameter == 'Last Month':
            return datetime.date.today() - datetime.timedelta(days=30)
        elif parameter == 'Last Three Months':
            return datetime.date.today() - datetime.timedelta(days=91)
        elif parameter == 'Last Six Months:':
            return datetime.date.today() - datetime.timedelta(days=183)
        elif parameter == 'Last Year':
            return datetime.date.today() - datetime.timedelta(days=365)
        else:
            return datetime.date.today() - datetime.timedelta(days=1000)

    def get_queryset(self):

        filters_instance = Filter.objects.last()
        # If no filters OR filters were set on different days OR 'NO FILTER' is clicked...
        if filters_instance is None or datetime.date.today() - filters_instance.last_update_date > datetime.timedelta(days=1):
            category_filter = ''
            time_filter = ''

        else:
            category_filter = filters_instance.category_filter
            time_filter = self.get_time_filter(filters_instance.time_filter)

        if category_filter == '' and time_filter != '':
            return Purchase.objects.filter(date__gte=time_filter).order_by('-date', '-time')

        elif category_filter != '' and time_filter == '':
            return Purchase.objects.filter(category=category_filter).order_by('-date', '-time')

        elif category_filter != '' and time_filter != '':
            return Purchase.objects.filter(date__gte=time_filter, category=category_filter).order_by('-date', '-time')

        else:
            return Purchase.objects.all()

@login_required
def filter_manager(request):

    if request.method == 'POST':

        filters_instance = Filter.objects.all()[0]

        filters_instance.last_update_date = datetime.date.today()
        filters_instance.last_update_time = datetime.datetime.now()

        if request.POST['filter'][0] == 'c':
            filters_instance.category_filter = request.POST['filter'][1:]
        elif request.POST['filter'][0] == 't':
            filters_instance.time_filter = request.POST['filter'][1:]

        else: # 'NO FILTER' was selected
            filters_instance.category_filter = ''
            filters_instance.time_filter = ''

        filters_instance.save()

        return HttpResponse()

    elif request.method == 'GET':

        try:
            filters_instance = Filter.objects.all()[0]

        except:

            Filter.objects.create(last_update_date = datetime.date.today(),
                                  last_update_time = datetime.datetime.now(),
                                  category_filter = '',
                                  time_filter = '' )

        return JsonResponse({'category_filter': filters_instance.category_filter,
                             'time_filter': filters_instance.time_filter})
