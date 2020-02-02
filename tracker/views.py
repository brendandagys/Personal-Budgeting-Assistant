from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from .forms import PurchaseForm
from .models import Purchase

import datetime
import re

def homepage(request):

    if request.method == 'GET':

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

    def get_date_filter(self, parameter):

        if parameter == 'LastWeek':
            return datetime.date.today() - datetime.timedelta(days=7)
        elif parameter == 'LastMonth':
            return datetime.date.today() - datetime.timedelta(days=30)
        elif parameter == 'LastThreeMonths':
            return datetime.date.today() - datetime.timedelta(days=91)
        elif parameter == 'LastSixMonths:':
            return datetime.date.today() - datetime.timedelta(days=183)
        elif parameter == 'LastYear':
            return datetime.date.today() - datetime.timedelta(days=365)
        else:
            return datetime.date.today() - datetime.timedelta(days=1000)

    def get_queryset(self):

        # URL that user was on when filter was clicked
        from_url = self.request.META.get('HTTP_REFERER')
        print(from_url)
        # print(self.request.META['HTTP_REFERER'])
        if from_url is not None and 'NO FILTER' not in self.request.path:

        # Find the filter settings from the old page
            try:
                match_date = re.search('.*transactions/(\w+)/.*', from_url).group(1)
            except Exception:
                match_date = None

            try:
                match_category = re.search('.*transactions/.*/(\w+)', from_url).group(1)
            except Exception:
                match_category = None

            # If there is one and no new one was specified...
            if match_date is not None and self.args[0] == '':
                date_filter = self.get_date_filter(match_date)
            # Otherwise process the URL parameter as normal
            else:
                 date_filter = self.get_date_filter(self.args[0])

            # To add on to the filter
            if match_category is not None and self.args[1] == '':
                category_filter = match_category
            else:
                category_filter = self.args[1]

        else:
            date_filter = datetime.date.today() - datetime.timedelta(days=1000)#self.get_date_filter(self.args[0])
            category_filter = ''#self.args[1]

        if category_filter == 'Medicine':
            category_filter = 'Drugs'

        print(date_filter)
        print(category_filter)

        if category_filter == '':

            return Purchase.objects.filter(date__gte=date_filter).order_by('-date', '-time')

        return Purchase.objects.filter(date__gte=date_filter, category=category_filter).order_by('-date', '-time')
        # return Purchase.objects.all()


def filter_manager(request):

    if request.method == 'GET':

        filters_instance = Filters.objects.last()

        if filters_instance is None or datetime.date.today() - filters_instance.last_update_date > 1:

            last_update_date = datetime.date.today()
            last_update_time = datetime.datetime.now()
            date_filter = ''
            time_filter = ''

            Filters.objects.create(last_update_date = datetime.date.today(),
                                   last_update_time = datetime.datetime.now(),
                                   date_filter = '',
                                   time_filter = ''
                                   )

        else:
            last_update_date = filters_instance.last_update_date
            last_last_update_time = filters_instance.last_update_time
            date_filter = filters_instance.date_filter
            time_filter = filters_instance.time_filter

            filters_instance.save()

        return JsonResponse({'last_update_date': last_update_date,
                             'last_update_time': last_update_time,
                             'date_filter': date_filter,
                             'time_filter': time_filter})


    elif request.method == 'POST': # Shouldn't need to TRY/EXCEPT or to save. Should be done on GET
        try:
            filters_instance = Filters.objects.all()[0]

            filters_instance.last_update_date = datetime.date.today()
            filters_instance.last_update_time = datetime.date.now()
            filters_instance.date_filter = request.POST.get('date_filter', '')
            filters_instance.time_filter = request.POST.get('time_filter', '')


            code_red_status_instance = CodeStatuses.objects.all()[0]

            code_red_status_instance.code_red_status = request.POST['code_red_status']
            code_red_status_instance.status_setter = request.POST['status_setter']

            try:
                code_red_status_instance.from_location = request.POST['from_location']
            except:
                code_red_status_instance.from_location = ''

            try:
                code_red_status_instance.to_location = request.POST['to_location']
            except:
                code_red_status_instance.to_location = ''

        except:
            code_red_status_instance = CodeStatuses()

        code_red_status_instance.save()

        return HttpResponse()
