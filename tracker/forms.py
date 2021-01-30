from django.forms import Form, ModelForm, DecimalField, NumberInput, CharField, Select, SelectMultiple

import datetime
from calendar import day_name
from django.utils import timezone

def current_date():
    return datetime.date.today()

from .models import Purchase, Account, AccountUpdate, Recurring, QuickEntry, Profile, PurchaseCategory


class PurchaseForm(ModelForm):
    def __init__(self, username=None, *args, **kwargs):
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

        user_categories = []

        for category in PurchaseCategory.objects.filter(user__username=username):
            user_categories.append(category.category)

        # The choices that display in the form field match models.py __str__ ... I want __str__ for Admin, but only the category text in the form field
        category_choices = []
        for choice in self.fields['category'].choices:
            if choice[0] == '': # First value is ('', '---------')
                category_choices.append((choice[0], choice[1]))
            elif choice[1].split(',')[0] == username and choice[1].split(', ')[1] in user_categories: # Filter to only that user's categories
                category_choices.append((choice[0], choice[1].split(', ')[1])) # (1, 'brendan, Coffee, None, 30 days')

        self.fields['category'].choices = category_choices
        self.fields['category_2'].choices = category_choices


    # def clean_time(self): # Will be a string of 0 - 4 numbers, no colon
    #     time_string = self.cleaned_data['time']
    #     time_string = time_string.replace(':', '')
    #
    #     if len(time_string) == 4:
    #         if time_string[0:2] in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
    #                                 '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
    #             if int(time_string[2]) in range(6) and int(time_string[3]) in range(10): # Normal time
    #                 return time_string[0:2] + ':' + time_string[2:4]
    #             else:
    #                 return time_string[0:2] + ':00' # If last two digits don't make sense, just save on the hour
    #
    #     elif len(time_string) == 1: # Number is enforced in the front-end
    #         return '0' + time_string + ':00'
    #
    #     elif len(time_string) == 2:
    #         if time_string in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
    #                            '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
    #             return time_string[0:2] + ':' + time_string[2:4]
    #
    #     elif len(time_string) == 3:
    #         if int(time_string[1:]) in range(60):
    #             return '0' + time_string[0] + ':' + time_string[1:]
    #         else:
    #             return '0' + time_string[0] + ':00'
    #
    #     return '00:00'

    class Meta:
        model = Purchase
        fields = ['date', 'time', 'category', 'item', 'amount', 'category_2', 'amount_2', 'description', 'currency', 'receipt']


class QuickEntryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuickEntryForm, self).__init__(*args, **kwargs)

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm green'})
            self.fields[field].label = ''

        self.fields['item'].widget.attrs.update({'placeholder': 'Item(s)...'})
        self.fields['amount'].widget.attrs.update({'placeholder': 'Amount...', 'inputmode': 'decimal'})
        self.fields['amount_2'].widget.attrs.update({'placeholder': 'Optional amount...', 'inputmode': 'decimal'})
        self.fields['description'].widget.attrs.update({'rows': 3, 'placeholder': 'Specifics...'})

        # The choices that display in the form field match models.py __str__ ... I want __str__ for Admin, but only the category text in the form field
        category_choices = []
        for choice in self.fields['category'].choices:
            if choice[0] == '': # First value is ('', '---------')
                category_choices.append((choice[0], choice[1]))
            else:
                category_choices.append((choice[0], choice[1].split(',')[1].strip())) # (1, 'brendan, Coffee, None, 30 days')
        self.fields['category'].choices = category_choices
        self.fields['category_2'].choices = category_choices

    class Meta:
        model = QuickEntry
        fields = ['category', 'item', 'amount', 'category_2', 'amount_2', 'description']


class ProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm green'})

    class Meta:
        model = Profile
        exclude = ['user']


class AccountForm(ModelForm):
    def __init__(self, user_object, *args, **kwargs): # Added user_object argument to __init__ !
        super(AccountForm, self).__init__(*args, **kwargs)

        user_object = user_object

        self.fields = {} # Otherwise a field will appear for each field in the model, but we want a specific field to show for each Account

        for account in Account.objects.filter(user=user_object).order_by('id'):
            if account.active:
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
        self.fields['dates'].widget = SelectMultiple(attrs={'class': 'form-control form-control-sm'},choices=((x, x) for x in range(1,32)))
        self.fields['weekdays'].widget = SelectMultiple(attrs={'class': 'form-control form-control-sm'},choices=((x, x) for x in day_name))
        self.fields['xth_from_specific_date'].widget = Select(attrs={'class': 'form-control form-control-sm'},choices=((x, x) for x in range(1,32)))
        self.fields['amount'].widget.attrs.update({'inputmode': 'decimal'})
        self.fields['number'].label = 'Every'
        self.fields['number'].widget.attrs.update({'inputmode': 'numeric'})
        self.fields['interval_type'].label = 'Unit'
        self.fields['xth_type'].label = 'Of'
        self.fields['xth_from_specific_date'].label = 'From This Date'
        self.fields['xth_after_months'].label = 'Every __ Months'
        self.fields['xth_after_months'].widget.attrs.update({'inputmode': 'numeric'})

        bills_id = None

        # The choices that display in the form field match models.py __str__ ... I want __str__ for Admin, but only the category text in the form field
        category_choices = []
        for choice in self.fields['category'].choices:
            if choice[0] == '': # First value is ('', '---------')
                category_choices.append((choice[0], choice[1]))
            else:
                category_choices.append((choice[0], choice[1].split(',')[1].strip())) # (1, 'brendan, Coffee, None, 30 days')

            if ',' in choice[1] and choice[1].split(',')[1].strip() == 'Bills':
                bills_id = choice[0]

        self.fields['category'].choices = category_choices

        if bills_id:
            self.fields['category'].initial = bills_id


    class Meta:
        model = Recurring
        exclude = ['user']
