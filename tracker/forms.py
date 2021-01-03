from django.forms import ModelForm, DateField, DecimalField, NumberInput, CharField, IntegerField # All added for ModelForms

import datetime
from django.utils import timezone

def current_date():
    return datetime.date.today()

from .models import Purchase, Account, AccountUpdate, Recurring


class PurchaseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseForm, self).__init__(*args, **kwargs)

        self.fields['account_to_use'] = CharField(required=False) # To indicate to not increment the credit card balance

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm green'})
            self.fields[field].label = ''

        self.fields['date'].widget.attrs.update({'placeholder': 'Date...', 'inputmode': 'numeric'})
        self.fields['time'].widget.attrs.update({'placeholder': 'Time...', 'inputmode': 'numeric'})
        self.fields['item'].widget.attrs.update({'placeholder': 'Item(s)...'})
        self.fields['amount'].widget.attrs.update({'placeholder': 'Amount...', 'inputmode': 'decimal'})
        self.fields['amount_2'].widget.attrs.update({'placeholder': 'Optional amount...', 'inputmode': 'decimal'})
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Specifics...'})
        self.fields['currency'].widget.attrs.update({'placeholder': 'Currency...'})

        # The choices that display in the form field match models.py __str__ ... I want __str__ for Admin, but only the category text in the form field
        category_choices = []
        for choice in self.fields['category'].choices:
            if choice[0] == '': # First value is ('', '---------')
                category_choices.append((choice[0], choice[1]))
            else:
                category_choices.append((choice[0], choice[1].split(',')[1].strip())) # (1, 'brendan, Coffee, None, 30 days')
        self.fields['category'].choices = category_choices
        self.fields['category_2'].choices = category_choices


    def clean_time(self): # Will be a string of 0 - 4 numbers, no colon
        time_string = self.cleaned_data['time']
        time_string = time_string.replace(':', '')

        if len(time_string) == 4:
            if time_string[0:2] in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
                                    '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
                if int(time_string[2]) in range(6) and int(time_string[3]) in range(10): # Normal time
                    return time_string[0:2] + ':' + time_string[2:4]
                else:
                    return time_string[0:2] + ':00' # If last two digits don't make sense, just save on the hour

        elif len(time_string) == 1: # Number is enforced in the front-end
            return '0' + time_string + ':00'

        elif len(time_string) == 2:
            if time_string in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
                               '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
                return time_string[0:2] + ':' + time_string[2:4]

        elif len(time_string) == 3:
            if int(time_string[1:]) in range(60):
                return '0' + time_string[0] + ':' + time_string[1:]
            else:
                return '0' + time_string[0] + ':00'

        return '00:00'

    class Meta:
        model = Purchase
        fields = ['date', 'time', 'category', 'item', 'amount', 'category_2', 'amount_2', 'description', 'currency', 'receipt']


class AccountForm(ModelForm):
    def __init__(self, user_object, *args, **kwargs): # Added user_object argument to __init__ !
        super(AccountForm, self).__init__(*args, **kwargs)

        user_object = user_object

        self.fields = {} # Otherwise a field will appear for each field in the model, but we want a specific field to show for each Account

        for account in Account.objects.filter(user=user_object).order_by('id'):
            # Get the last value for the account. If it's None, make placeholder value 0
            last_value = 0 if AccountUpdate.objects.filter(account=account).order_by('-timestamp').first() is None else AccountUpdate.objects.filter(account=account).order_by('-timestamp').first().value
            self.fields[account.account] = DecimalField(label=account.account, max_digits=9, decimal_places=2, localize=False, widget=NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'width:180px',
                                                                                                                                                    'inputmode': 'decimal', 'placeholder': '${:20,.2f}'.format(last_value)}))

    class Meta:
        model = Account
        exclude = []


class RecurringForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(RecurringForm, self).__init__(*args, **kwargs)

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm', 'style': 'width:13rem'})

        self.fields['description'].widget.attrs.update({'rows': 2})

    class Meta:
        model = Recurring
        exclude = []
