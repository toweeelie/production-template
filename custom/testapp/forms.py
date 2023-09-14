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


class InitSkatingCalculatorForm(forms.Form):
    '''
    Form for adding judjes into Skating Calculator
    '''
    competitors = forms.IntegerField(label=_('Competitors'),widget=forms.NumberInput(attrs={'style': 'width: 50px'}),min_value=0)
    judges = forms.IntegerField(label=_('Judges'),widget=forms.NumberInput(attrs={'style': 'width: 50px'}),min_value=0)

class SkatingCalculatorForm(forms.Form):
    '''
    Main Skating Calculator Form
    '''
    outType = forms.ChoiceField(widget=forms.RadioSelect, choices=[('1', 'inplace'), ('2', 'csv')], label=_('Results format:'))

    def __init__(self, *args, **kwargs):
        self.judges = kwargs.pop('judges', 0)
        self.competitors = kwargs.pop('competitors', 0)

        super(SkatingCalculatorForm, self).__init__(*args, **kwargs)
      
        for cidx in range(0,self.competitors):
            self.fields['c{0}'.format(cidx)] = forms.CharField(label='',widget=forms.TextInput(attrs={'style': 'width: 140px'}))

        for jidx in range(0,self.judges):
            self.fields['j{0}'.format(jidx)] = forms.CharField(label='',widget=forms.TextInput(attrs={'style': 'width: 70px'}))
            for cidx in range(0,self.competitors):
                self.fields['p{0}_{1}'.format(jidx,cidx)] = forms.IntegerField(label='',widget=forms.NumberInput(attrs={'style': 'width: 70px'}),min_value=1,max_value=self.competitors)

    def clean(self):
        cleaned_data = super().clean()

        # check if there is no duplicated points in each judge column
        for jidx in range(0,self.judges):
            points = [ cleaned_data['p{0}_{1}'.format(jidx,cidx)] for cidx in range(0,self.competitors) ]
            if len(points) != len(set(points)):
                raise ValidationError(_('Judge {0} has points duplication').format(cleaned_data['j{0}'.format(jidx)]))

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


from danceschool.core.models import Customer,DanceRole
from .models import Competition,Registration
from django.utils.html import format_html

class CompetitionRegForm(forms.Form):
    '''
    Form for competition registration
    '''
    first_name = forms.CharField(max_length=100,label=_('First Name'))
    last_name = forms.CharField(max_length=100,label=_('Last Name'))
    email = forms.EmailField(max_length=100,label=_('Email'))
    comp_role = forms.ChoiceField(choices=[],label=_('Dance Role'))

    class Meta:
        model = Customer
        fields = ('first_name','last_name','email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        comp = self.initial.get('comp')
        if comp:
            comp_roles = comp.comp_roles.all()
            self.fields['comp_role'].choices = [('',''),]
            self.fields['comp_role'].choices += [(role.id, role.name) for role in comp_roles]

        user = self.initial.get('user')
        if user.is_authenticated:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

class PrelimsResultsForm(forms.Form):
    '''
    Form for prelims results
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        registrations = self.initial.get('registrations')
        for registration in registrations:
            if registration.comp_checked_in:
                self.fields[f'competitor_{registration.comp_num}'] = forms.ChoiceField(
                    label=f'{registration.comp_num} {registration.competitor.fullName}',
                    choices=[
                        ('no', ''),
                        ('maybe', 'Mb'),
                        ('yes', 'Y'),
                    ],
                    required=True,
                )
                self.fields[f'comment_{registration.comp_num}'] = forms.CharField(
                    label='',
                    max_length=100,
                    widget=forms.TextInput(attrs={'placeholder':'Comments','style': 'width: 100%'}),
                    required=False,
                )

    def clean(self):
        cleaned_data = super().clean()
        results = [res for field,res in cleaned_data.items() if field.startswith('competitor_')]
        comp = self.initial.get('comp')

        # check if enough Y and Mb were choosen
        if results and comp:
            Y_num = comp.finalists_number-1
            count_y = results.count('yes')
            count_mb = results.count('maybe')
            if count_y != Y_num or count_mb != 2:
                raise ValidationError(_(f"There should be {Y_num} 'Y' and 2 'Mb' marks"))
            
        return cleaned_data
    

class FinalsResultsForm(forms.Form):
    '''
    Form for prelims results
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        registrations = self.initial.get('registrations')
        comp = self.initial.get('comp')
        for registration in registrations:
            self.fields[f'competitor_{registration.comp_num}'] = forms.IntegerField(
                label=f'{registration.comp_num}/{registration.final_partner.comp_num} '+
                    f'{registration.competitor.first_name} - '+
                    f'{registration.final_partner.competitor.first_name}',
                    #f'{registration.competitor.first_name}{registration.competitor.last_name[0]} - '+
                    #f'{registration.final_partner.competitor.first_name}{registration.final_partner.competitor.last_name[0]}',
                min_value=1,
                max_value=comp.finalists_number,
                required=True,
            )
            self.fields[f'comment_{registration.comp_num}'] = forms.CharField(
                label='',
                max_length=100,
                widget=forms.TextInput(attrs={'placeholder':'Comments','style': 'width: 100%'}),
                required=False,
            )

    def clean(self):
        cleaned_data = super().clean()
        results = [res for field,res in cleaned_data.items() if field.startswith('competitor_')]
        comp = self.initial.get('comp')

        # check if results are unique
        if results and comp:
            if len(results) != len(set(results)):
                raise ValidationError(_(f"Places duplication"))
            
        return cleaned_data