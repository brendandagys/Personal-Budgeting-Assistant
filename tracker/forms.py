from django import forms
from django.forms import ModelForm, Textarea, CharField, EmailField, ChoiceField # All added for ModelForms

import datetime
from django.utils import timezone

from .models import Purchase


class PurchaseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm green'})

        self.fields['item'].widget.attrs.update({'placeholder': 'Item(s)...'})
        self.fields['amount'].widget.attrs.update({'placeholder': 'Amount...'})
        self.fields['amount_2'].widget.attrs.update({'placeholder': 'Optional...'})
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Specifics...'})

    class Meta:
        model = Purchase
        fields = ['date', 'time', 'item', 'category', 'amount', 'amount_2', 'description']


#         def clean_date(self):
#             return self.cleaned_data['date']
#
#         def clean_time(self):
#             return self.cleaned_data['time']
#
#         def clean_item(self):
#             return self.cleaned_data['item']
#
#         def clean_category(self):
#             return self.cleaned_data['category']
#
#         def clean_amount(self):
#             return self.cleaned_data['amount']
#
#         def clean_category_2(self):
#             return self.cleaned_data['category_2']
#
#         def clean_amount_2(self):
#             return self.cleaned_data['amount_2']
#
#         def clean_description(self):
#             return self.cleaned_data['description']
