from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from .forms import PurchaseForm
from .models import Purchase, Filter, Bill

import datetime
import re

def homepage(request):

    if request.method == 'GET':

        date = datetime.date.today()
        year = date.year
        month = date.month
        day = date.day

        apple_music_instance = Bill.objects.filter(bill='apple_music')[-1:]
        if len(apple_music_instance) == 0 or apple_music_instance.last_update_date.month != month:
            Bill.objects.create(bill = 'Apple Music', last_update_date = date)

        try:
            bills_instance = Bill.objects.all[0]
        except:
            bills_instance = Bill.objects.create(bill = '', last_update_date = '')



        purchase_form = PurchaseForm()

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

        return JsonResponse({ 'category_filter': filters_instance.category_filter,
                              'time_filter': filters_instance.time_filter })
