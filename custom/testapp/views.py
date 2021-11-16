from django.views.generic import (
    FormView, CreateView, UpdateView, DetailView, TemplateView, ListView,
    RedirectView
)

from django.urls import reverse
from django.http import HttpResponseBadRequest,HttpResponseRedirect,HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from braces.views import UserFormKwargsMixin, PermissionRequiredMixin, LoginRequiredMixin, StaffuserRequiredMixin
from danceschool.core.models import Customer
from danceschool.core.views import EventRegistrationSummaryView
from .forms import QuickCustomerRegForm, MergeCustomersForm, SkatingCalculatorForm, InitSkatingCalculatorForm

import unicodecsv as csv

#from danceschool.core.constants import getConstant, INVOICE_VALIDATION_STR
from danceschool.core.models import Invoice, CashPaymentRecord, Registration, EventRegistration, DanceRole
from danceschool.core.constants import getConstant
from danceschool.core.helpers import getReturnPage

import logging

# Define logger for this file
logger = logging.getLogger(__name__)


class QuickCustomerRegView(FormView):
    form_class = QuickCustomerRegForm
    
    def form_valid(self, form):
        payLater = form.cleaned_data.get('payLater')
        amountPaid = form.cleaned_data.get('amountPaid')
        subUser = form.cleaned_data.get('submissionUser')
        payerEmail = form.cleaned_data.get('payerEmail')
        receivedBy = form.cleaned_data.get('receivedBy')
        event = form.cleaned_data.get('event')
        customer = form.cleaned_data.get('customer')
        role = form.cleaned_data.get('role')
        dropIn = form.cleaned_data.get('dropIn')
        expiry = timezone.now() + timedelta(minutes=getConstant('registration__sessionExpiryMinutes'))

        reg = Registration(
                submissionUser=subUser, dateTime=timezone.now(),
                payAtDoor=payLater,
            )

        invoice = reg.link_invoice(expirationDate=expiry)
        reg.save()

        tr = EventRegistration(
                customer=customer, event=event, dropIn=dropIn #, role_id=role
            )

        tr.registration = reg
        tr.save()

        if payLater == True:
            instance = form.cleaned_data.get('instance')

            invoice.status = Invoice.PaymentStatus.unpaid
            invoice.save()

            if getattr(invoice, 'registration', None):
                invoice.registration.finalize()
                #return HttpResponseRedirect(self.get_success_url())
                #return self.render_to_response(self.get_context_data(form = form))
                return HttpResponseRedirect(reverse('viewregistrations',
                                                    kwargs={'event_id':event.id}))
            if instance:
                return HttpResponseRedirect(instance.successPage.get_absolute_url())
        else:

            paymentMethod = form.cleaned_data.get('paymentMethod')

            if not invoice:
                return HttpResponseBadRequest("No invoice")

            this_cash_payment = CashPaymentRecord.objects.create(
                invoice=invoice, amount=amountPaid,
                status=CashPaymentRecord.PaymentStatus.collected,
                paymentMethod=paymentMethod,
                payerEmail=payerEmail,
                submissionUser=subUser, collectedByUser=receivedBy,
            )
            invoice.processPayment(
                amount=amountPaid, fees=0, paidOnline=False, methodName=paymentMethod,
                submissionUser=subUser, collectedByUser=receivedBy,
                methodTxn='CASHPAYMENT_%s' % this_cash_payment.recordId,
                forceFinalize=True,
            )
            return HttpResponseRedirect(reverse('registration'))

    def form_invalid(self, form):
        return HttpResponseBadRequest(str(form.errors))

class MergeCustomersView(PermissionRequiredMixin, FormView):
    form_class = MergeCustomersForm
    permission_required = 'core.view_registration_summary'
    template_name = 'core/merge_customers.html'

    def dispatch(self, request, *args, **kwargs):
        ''' If a list of customers or groups was passed, then parse it '''
        ids = request.GET.get('customers').split(', ')
        self.customers = None

        if len(ids) > 1:
            # Initial filter applies to no one but allows appending by logical or
            filters = Q(id__isnull=True)
            filters = filters | Q(id__in=[int(x) for x in ids])

            try:
                self.customers = Customer.objects.filter(filters)
            except ValueError:
                return HttpResponseBadRequest(_('Invalid customer ids passed'))
        else:
            return HttpResponseBadRequest(_('Nothing to merge'))
        return super(MergeCustomersView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        ''' Tell the form which fields to render '''
        kwargs = super().get_form_kwargs(**kwargs)
        #kwargs['user'] = self.request.user if hasattr(self.request, 'user') else None
        kwargs['customers'] = self.customers
        return kwargs

    def form_valid(self, form):
        ''' Set all fields from a form for first customer record in a list'''
        for val_name, idx in form.cleaned_data.items():
            if int(idx) != 0:
                setattr(self.customers[0],val_name,getattr(self.customers[int(idx)],val_name))

        ''' Change all related records to match new customer id and delete old record '''

        

        return HttpResponseRedirect(reverse('admin:core_customer_changelist'))

# EventRegistrationSummaryView.context['form'] = QuickCustomerRegForm

class SkatingCalculatorView(FormView):
    form_class = SkatingCalculatorForm
    template_name = 'sc/skating_calculator.html'
    success_url = '/skatingcalculator'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['init_form'] = InitSkatingCalculatorForm
        return context

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs['judges'] = self.request.session.get('judges',0)
        kwargs['competitors'] = self.request.session.get('competitors',0)
        return kwargs

    def init_tab(request):
        if request.method == "POST":
            form = InitSkatingCalculatorForm(request.POST)
            if form.is_valid():
                request.session['judges'] = form.cleaned_data.get('judges')
                request.session['competitors'] = form.cleaned_data.get('competitors')
        return HttpResponseRedirect(reverse('skatingCalculator'))

    def form_valid(self, form):
        judges = self.request.session.get('judges',0)
        competitors = self.request.session.get('competitors',0)

        sctable = []    
        # write header
        sctable.append(['',]+[form.cleaned_data['j{0}'.format(jidx)] for jidx in range(0,judges)] + ['"1-{0}"'.format(p) for p in range(1,competitors+1)] + [_('Place'),])

        for cidx in range(competitors):
            # get points specific for competitor
            points = [ form.cleaned_data['p{0}_{1}'.format(jidx,cidx)] for jidx in range(0,judges) ]

            # count points entries
            entries = [points.count(1),]
            for e in range(2,competitors+1):
                entries.append(points.count(e)+entries[-1])

            # append row specific for competitor 
            sctable.append([form.cleaned_data['c{0}'.format(cidx)],] + points + entries)

        # define recursive skating procedure
        def skating_rules(init_col,place,sub_sctable):
            # go over entries columns
            for pcol in range(init_col,competitors): 
                # get list of (entry,sum,idx)
                column = []
                for cidx,comp in sub_sctable.items():
                    # place is not set yet
                    if len(comp) != len(sctable[0]):
                        # entry is >= majority
                        if comp[judges+1+pcol] >= majority:
                            column.append((-comp[judges+1+pcol],sum([c for c in comp[1:judges+1] if c <= pcol+1]),cidx))
                            
                # go over a list sorted descending by occurences then ascending by sums
                for cval,csum,cidx in sorted(column): 
                    # if current (entry,sum) is unique
                    if [(c[0],c[1]) for c in column].count((cval,csum)) == 1:
                        # assign the place
                        for p in range(pcol+1,competitors):
                            sctable[cidx+1][judges+1+p] = 0
                        sctable[cidx+1].append(place)
                        place += 1
                        # set sum tiebreaker if found equal entries
                        if [c[0] for c in column].count(cval) != 1:
                            sctable[cidx+1][judges+1+pcol] = str(sctable[cidx+1][judges+1+pcol]) + '(%d)' % csum
                    # process only if place is not assigned for current competitor
                    elif len(sctable[cidx+1]) != len(sctable[0]):
                        # collect indexes of all equal cases
                        equal_indexes =  [c[2] for c in column if c[0] == cval and c[1] == csum ]
                        # write sums to show that there was no tiebreaker on this column
                        for eidx in equal_indexes:
                            sctable[eidx+1][judges+1+pcol] = str(sctable[eidx+1][judges+1+pcol]) + '(%d)' % csum
                        # process search across the rest of the table for equal cases
                        place = skating_rules(pcol+1, place, { i:l for i,l in sub_sctable.items() if i in equal_indexes })

            # reached the end of the table, share several places among all equal cases
            if init_col == competitors:
                shared_places = '/'.join(map(str,range(place,place+len(sub_sctable))))
                for cidx in sub_sctable.keys():
                    sctable[cidx+1].append(shared_places)
                place += len(sub_sctable)
            return place

        # calculate places
        majority = int(judges/2)+1
        skating_rules(0, 1, { i:l for i,l in enumerate(sctable[1:]) })

        # clean zeroes from the table
        for ridx, row in enumerate(sctable):
            for cidx, cell in enumerate(row):
                if sctable[ridx][cidx] == 0:
                    sctable[ridx][cidx] = ''

        if form.cleaned_data['outType'] == '1':
            # display results inplace
            return self.render_to_response(
                self.get_context_data(
                    form = form,
                    skating = list(zip(*sctable))[judges+1:] # transpose the table and get only "entries+place" part
                )
            )
        else: 
            # write table to csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="skating.csv"'

            writer = csv.writer(response, csv.excel)
            response.write(u'\ufeff'.encode('utf8'))

            for row_data in sctable: 
                writer.writerow(row_data)

            return response
