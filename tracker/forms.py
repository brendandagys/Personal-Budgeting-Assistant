from django.forms import ModelForm, DecimalField, NumberInput #, Textarea, CharField, EmailField, ChoiceField # All added for ModelForms

import datetime
from django.utils import timezone

from .models import Purchase, Account, AccountUpdate


class PurchaseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm green'})

        self.fields['item'].widget.attrs.update({'placeholder': 'Item(s)...'})
        self.fields['amount'].widget.attrs.update({'placeholder': 'Amount...', 'inputmode': 'decimal'})
        self.fields['amount_2'].widget.attrs.update({'placeholder': 'Optional...', 'inputmode': 'decimal'})
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Specifics...'})
        self.fields['currency'].widget.attrs.update({'placeholder': 'Currency...'})

        # The choices that display in the form field match models.py __str__ ... I want __str__ for Admin, but only the category text in the form field
        category_choices = []
        for choice in self.fields['category'].choices:
            category_choices.append((choice[0], choice[1].split(',')[0])) # (1, 'Coffee, None, 30, 2020-12-12 18:39:00')
        self.fields['category'].choices = category_choices
        self.fields['category_2'].choices = category_choices

    class Meta:
        model = Purchase
        fields = ['date', 'time', 'category', 'item', 'amount', 'category_2', 'amount_2', 'description', 'currency']


class AccountForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)

        self.fields = {} # Otherwise a field will appear for each field in the model, but we want a specific field to show for each Account

        for account in Account.objects.all().order_by('id'):
            # Get the last value for the account. If it's None, make placeholder value 0
            last_value = 0 if AccountUpdate.objects.filter(account=account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=account).order_by('-timestamp').first().value
            self.fields[account.pk] = DecimalField(label=account.account, max_digits=9, decimal_places=2, localize=False, widget=NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:180px',
                                                                                                                                                         'inputmode': 'decimal', 'placeholder': '${:20,.2f}'.format(last_value)}))

    class Meta:
        model = Account
        exclude = []
