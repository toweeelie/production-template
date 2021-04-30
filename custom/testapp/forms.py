from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import F, Q, Value, CharField
from dal import autocomplete
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from danceschool.core.models import Customer, User, Event, Series
from django.core.exceptions import ValidationError

class QuickCustomerRegForm(forms.Form):
    '''
    This form can be used to quickly register customers on selected event
    '''

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=#RelatedFieldWidgetWrapper(
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
            #rel=Series._meta.get_field('classDescription').remote_field,
            #admin_site=None,
            #can_add_related=True,
            #can_change_related=True,
        #)
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        event = kwargs.pop('object', None)
        subUser = getattr(user, 'id', None)
        fullSeriesPrice = getattr(event, 'basePrice', None)
        kwargs.update(initial={
            'receivedBy': subUser,
            'amountPaid' : fullSeriesPrice,
            'event' : event
        })

        super(QuickCustomerRegForm, self).__init__(*args, **kwargs)

        setattr(self.fields['role'],'choices',
            [(i,x) for i,x in enumerate(getattr(event, 'availableRoles',['L','F']))])

        #setattr(getattr(self.fields['customer'],'widget',None),'admin_site',self.admin_site)

    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'autocomplete_light/jquery.init.js',
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
