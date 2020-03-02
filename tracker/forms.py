from django import forms

import datetime
from django.utils import timezone

from .models import Purchase


class PurchaseForm(forms.Form):

        CATEGORY_CHOICES = (
            ('', ''),
            ('Coffee', 'Coffee'),
            ('Groceries', 'Groceries'),
            ('Food/Drinks', 'Food/Drinks'),
            ('Restaurants', 'Restaurants'),
            ('Gas', 'Gas'),
            ('Bills', 'Bills'),
            ('Household Supplies', 'Household Supplies'),
            ('Services', 'Services'),
            ('Dates', 'Dates'),
            ('Gifts', 'Gifts'),
            ('Tickets', 'Tickets'),
            ('Electronics', 'Electronics'),
            ('Appliances', 'Appliances'),
            ('Clothes', 'Clothes'),
            ('Alcohol', 'Alcohol'),
            ('Vacation', 'Vacation'),
            ('Fees', 'Fees')
        )

        # required argument is True by default
        date = forms.DateField(label='Date:', initial=lambda: datetime.date.today(), widget=forms.TextInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                  'placeholder': 'Date (yyyy-mm-dd)...'}))

        time = forms.CharField(label='Time (24 hr.)', initial=lambda: str(timezone.now().time())[0:5], widget=forms.TimeInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                     'placeholder': 'Time...'}))

        amount = forms.DecimalField(label='Amount', max_digits=7, decimal_places=2, localize=False, widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                     'placeholder': 'Amount...'}))
        category = forms.ChoiceField(label='Category', choices=CATEGORY_CHOICES)

        category_2 = forms.ChoiceField(required=False, label='Category', choices=CATEGORY_CHOICES)

        item = forms.CharField(label='Item(s)', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm',
                                                                              'placeholder': 'Item...'}))

        description = forms.CharField(required=False, label='Information', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                                                                                        'placeholder': 'Specifics...'}))

        def clean_date(self):
            return self.cleaned_data['date']

        def clean_time(self):
            return self.cleaned_data['time']

        def clean_amount(self):
            return self.cleaned_data['amount']

        def clean_category(self):
            return self.cleaned_data['category']

        def clean_category_2(self):
            return self.cleaned_data['category_2']

        def clean_item(self):
            return self.cleaned_data['item']

        def clean_description(self):
            return self.cleaned_data['description']
