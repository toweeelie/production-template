from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import F, Q, Value, CharField
from dal import autocomplete
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from danceschool.core.models import Customer, User, Event, EventOccurrence, Series
from django.core.exceptions import ValidationError
from django_addanother.widgets import AddAnotherWidgetWrapper
from django.urls import reverse_lazy
from datetime import datetime

class QuickCustomerRegForm(forms.Form):
    '''
    This form can be used to quickly register customers on selected event
    '''

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget = AddAnotherWidgetWrapper(
                    autocomplete.ModelSelect2(
                        url='autocompleteCustomer',
                        attrs={
                            # This will set the input placeholder attribute:
                            'data-placeholder': _('Enter a customer name'),
                            # This will set the yourlabs.Autocomplete.minimumCharacters
                            # options, the naming conversion is handled by jQuery
                            'data-minimum-input-length': 2,
                            'data-max-results': 4,
                            'class': 'modern-style',
                        }
                    ),
                    reverse_lazy('admin:core_customer_add'),
        )
    )

    role = forms.ChoiceField(
        label=_('Dance Role'),
        widget=forms.RadioSelect,
        #choices=[('0','L'),('1','F')]
    )

    dropIn = forms.BooleanField(label=_('Drop-In'), required=False)

    payLater = forms.BooleanField(label=_('Pay Later'), required=False)

    amountPaid = forms.FloatField(label=_('Amount Paid'), required=False)

    receivedBy = forms.ModelChoiceField(
        queryset=User.objects.filter(Q(staffmember__isnull=False) | Q(is_staff=True)),
        label=_('Payment received by:'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='autocompleteUser',
            attrs={
                # This will set the input placeholder attribute:
                'data-placeholder': _('Enter a staff member name'),
                # This will set the yourlabs.Autocomplete.minimumCharacters
                # options, the naming conversion is handled by jQuery
                'data-minimum-input-length': 2,
                'data-max-results': 4,
                'class': 'modern-style',
            }
        )
    )

    event = forms.ModelChoiceField(
        queryset=Event.objects.all(), 
        required=True, 
        widget = forms.HiddenInput()
    )

    eventOccurrence = forms.ModelChoiceField(
        queryset=EventOccurrence.objects.all(), 
        required=True, 
        widget = forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        event = kwargs.pop('object', None)
        subUser = getattr(user, 'id', None)
        fullSeriesPrice = getattr(event, 'basePrice', None)
        eventOccurrence = getattr(event, 'nextOccurrenceForToday', None)
        kwargs.update(initial={
            'receivedBy': subUser,
            'amountPaid' : fullSeriesPrice,
            'event' : event,
            'eventOccurrence' : eventOccurrence,
        })

        super(QuickCustomerRegForm, self).__init__(*args, **kwargs)

        if event == None:
            event = Event.objects.get(id=kwargs['data']['event'])
        setattr(self.fields['role'],'choices',
            [(int(x.order),x) for x in getattr(event, 'availableRoles')])

    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'js/quick_reg.js',
        )

class MergeCustomersForm(forms.Form):
    '''
    This form can be used to merge duplicate customers records 
    '''

    def __init__(self, *args, **kwargs):
        customers = kwargs.pop('customers', [])

        super(MergeCustomersForm, self).__init__(*args, **kwargs)

        for f in Customer._meta.fields:
            self.fields[f.name] = forms.ChoiceField(
                label=f.verbose_name,
                #widget=forms.RadioSelect,
                choices=[(i,getattr(x, f.name)) for i,x in enumerate(customers)],
            )

class ProfileChooseDateForm(forms.Form):
    '''
    This form helps customers to view their monthly stats
    '''
    startDate = forms.DateField(
        label = '',
        initial = datetime.now(),
        #widget = forms.SelectDateWidget(
        #    years=range(2010,datetime.now().year+1),
        #),
        widget = forms.DateInput(attrs={'type': 'text'})
    )
    endDate = forms.DateField(
        label = '',
        initial = datetime.now(),
        widget = forms.DateInput(attrs={'type': 'text'})
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial['startDate'] = kwargs.pop('startDate', datetime.now().replace(day=1))
        initial['endDate'] = kwargs.pop('endDate', datetime.now())
        kwargs['initial'] = initial
        super(ProfileChooseDateForm, self).__init__(*args, **kwargs)
