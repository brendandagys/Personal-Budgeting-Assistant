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

import datetime
import re

@login_required
def homepage(request):

    bill_information = {
    'Apple Music': [7, 'Apple Music', 5.64, 'Monthly fee for Apple Music subscription.'],
    'Cell Phone': [13, 'Cell Phone Plan', 41.81, 'Monthly fee for cell phone plan with Public Mobile.'],
    'Car Insurance': [15, 'Car Insurance', 137.91, 'Monthly fee for car insurance with TD Meloche.'],
    'Rent': [1, 'Rent', 750.00, 'Monthly rent for apartment.'],
    }

    if request.method == 'GET':

        # Get information about today's date
        date = datetime.date.today()
        year = date.year
        month = date.month
        day = date.day
        # Get all bill instances
        apple_music_instance = Bill.objects.filter(bill='Apple Music').order_by('-last_update_date') # Querysets can return zero items
        cell_phone_instance = Bill.objects.filter(bill='Cell Phone').order_by('-last_update_date')
        car_insurance_instance = Bill.objects.filter(bill='Car Insurance').order_by('-last_update_date')
        rent_instance = Bill.objects.filter(bill='Rent').order_by('-last_update_date')

        def check_bill_payments(bill, instance):
            # Will create a Purchase object if True, since the month will match in the second if-statement
            instance_created_flag = False
            # If an instance doesn't exist, create it
            if len(instance) == 0:
                instance = Bill.objects.create(bill = bill, last_update_date = datetime.datetime(year, month, bill_information[bill][0]))
                instance_created_flag = True
            else:
                instance = instance[0] # instance is either a Queryset or a real instance. This ensures it always becomes the latter
            # Check if bills for the current month have been recorded
            if (instance.last_update_date.month != month and day > instance.last_update_date.day) or instance_created_flag is True:
                instance.last_update_date = datetime.datetime(year, month, bill_information[bill][0]) # Update the date. Won't matter if instance was just created

                Purchase.objects.create(date = datetime.datetime(year, month, bill_information[bill][0]),
                                        time = '00:00',
                                        amount = bill_information[bill][2],
                                        category = 'Bills',
                                        item = bill,
                                        description = bill_information[bill][3] )

        check_bill_payments('Apple Music', apple_music_instance)
        check_bill_payments('Cell Phone', cell_phone_instance)
        check_bill_payments('Car Insurance', car_insurance_instance)
        check_bill_payments('Rent', rent_instance)

        # Create a new form
        purchase_form = PurchaseForm()

    elif request.method == 'POST':

        def send_email():
            email_body = 'Test'
            email_message = EmailMessage('Spending Alert', email_body, from_email='Spending Helper <spendinghelper@gmail.com', to=['brendandagys@gmail.com'])
            email_message.content_subtype = 'html'
            email_message.send()

        send_email()

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

            purchase_instance.save()

            # This returns a blank form, to clear for the next submission
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

    @login_required
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
