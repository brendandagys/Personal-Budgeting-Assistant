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
        self.fields['amount'].widget.attrs.update({'placeholder': 'Amount...'})
        self.fields['amount_2'].widget.attrs.update({'placeholder': 'Optional...'})
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Specifics...'})

    class Meta:
        model = Purchase
        fields = ['date', 'time', 'item', 'category', 'amount', 'category_2', 'amount_2', 'description']


class AccountForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)

        self.fields = {} # Otherwise a field will appear for each field in the model, but we want a specific field to show for each Account

        for account in Account.objects.all():
            # Get the last value for the account. If it's None, make placeholder value 0
            last_value = 0 if AccountUpdate.objects.filter(account=account).order_by('timestamp').last() is None else AccountUpdate.objects.filter(account=account).order_by('timestamp').last().value
            self.fields[account.account] = DecimalField(label=account.account, max_digits=9, decimal_places=2, localize=False, widget=NumberInput(attrs={'class': 'form-control form-control-sm',
                                                                                                                                                         'placeholder': '${:20,.2f}'.format(last_value)}))

    class Meta:
        model = Account
        exclude = []
