from django import forms

import datetime
from django.utils import timezone

from .models import Purchase


class PurchaseForm(forms.Form):

        CATEGORY_CHOICES = (
            ('Unspecified', 'Category...'),
            ('Groceries', 'Groceries'),
            ('Fast Food', 'Fast Food'),
            ('Samantha', 'Samantha'),
            ('Dates', 'Dates'),
            ('Coffee', 'Coffee'),
            ('Gas', 'Gas'),
            ('Household Supplies', 'Household Supplies'),
            ('Clothes', 'Clothes'),
            ('Sex', 'Sex'),
            ('Drugs', 'Drugs'),
            #('', ''),
        )
        # To program:
        #   Cell phone bill
        #   Car insurance
        #   Apple Music
        #   Rent

        # required argument is True by default
        date = forms.DateField(label='Date:', initial=lambda: datetime.date.today(), widget=forms.TextInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                  'placeholder': 'Date (yyyy-mm-dd)...'}))

        time = forms.CharField(label='Time (24 hr.)', initial=lambda: str(timezone.now().time())[0:5], widget=forms.TimeInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                     'placeholder': 'Time...'}))

        amount = forms.DecimalField(label='Amount', max_digits=7, decimal_places=2, localize=False, widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                     'placeholder': 'Amount...'}))
        category = forms.ChoiceField(label='Category', choices=CATEGORY_CHOICES)

        item = forms.CharField(label='Item(s)', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm',
                                                                              'placeholder': 'Item...'}))

        description = forms.CharField(required=False, label='Description', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                                                                                        'placeholder': 'Specifics...'}))

        def clean_date(self):
            return self.cleaned_data['date']

        def clean_time(self):
            return self.cleaned_data['time']

        def clean_amount(self):
            return self.cleaned_data['amount']

        def clean_category(self):
            return self.cleaned_data['category']

        def clean_item(self):
            return self.cleaned_data['item']

        def clean_description(self):
            return self.cleaned_data['description']
