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
        if from_url is not None:

        # Find the filter settings from the old page
            match_date = re.search('transactions/(\w+)/', from_url)
            match_category = re.search('transactions/\w+/(\w+)/', from_url)

            # If there is one and no new one was specified...
            if match_date is not None and self.args[0] == '':
                date_filter = self.get_date_filter(match_date.group(1))
            # Otherwise process the URL parameter as normal
            else:
                 date_filter = self.get_date_filter(self.args[0])

            if match_category is not None and self.args[1] == '':
                category_filter = match_category.group(1)
            else:
                category_filter = self.args[1]

        else:
            date_filter = self.get_date_filter(self.args[0])
            category_filter = self.args[1]


        if category_filter == '':

            return Purchase.objects.filter(date__gte=date_filter).order_by('-date', '-time')

        return Purchase.objects.filter(date__gte=date_filter, category=category_filter).order_by('-date', '-time')
        # return Purchase.objects.all()
