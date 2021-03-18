from django.views.generic import (
    FormView, CreateView, UpdateView, DetailView, TemplateView, ListView,
    RedirectView
)

from django.urls import reverse
from django.http import HttpResponseBadRequest,HttpResponseRedirect,HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from braces.views import UserFormKwargsMixin, PermissionRequiredMixin, LoginRequiredMixin, StaffuserRequiredMixin
from danceschool.core.models import Customer
from danceschool.core.views import EventRegistrationSummaryView
from .forms import QuickCustomerRegForm, MergeCustomersForm, SkatingCalculatorForm, InitSkatingCalculatorForm

import unicodecsv as csv

#from danceschool.core.constants import getConstant, INVOICE_VALIDATION_STR
from danceschool.core.models import Invoice#, TemporaryRegistration, CashPaymentRecord
#from danceschool.core.helpers import getReturnPage

import logging

# Define logger for this file
logger = logging.getLogger(__name__)


def handle_quickreg(request):
    logger.info('Received request for quickreg at the door.')
    form = QuickCustomerRegForm(request.POST)
    if form.is_valid():
        payLater = form.cleaned_data.get('payLater')
        if payLater == True:
            tr = form.cleaned_data.get('registration')
            instance = form.cleaned_data.get('instance')

            invoice = Invoice.get_or_create_from_registration(
                tr,
                submissionUser=form.cleaned_data.get('submissionUser'),
            )
            invoice.finalRegistration = tr.finalize()
            invoice.save()
            if instance:
                return HttpResponseRedirect(instance.successPage.get_absolute_url())
        else:
            tr = form.cleaned_data.get('registration')
            invoice = form.cleaned_data.get('invoice')
            amountPaid = form.cleaned_data.get('amountPaid')
            subUser = form.cleaned_data.get('submissionUser')
            event = form.cleaned_data.get('event')
            sourcePage = form.cleaned_data.get('sourcePage')
            paymentMethod = form.cleaned_data.get('paymentMethod')
            payerEmail = form.cleaned_data.get('payerEmail')
            receivedBy = form.cleaned_data.get('receivedBy')

            if not tr and not invoice:
                return HttpResponseBadRequest()

            if not invoice:
                invoice = Invoice.get_or_create_from_registration(
                    tr,
                    submissionUser=subUser,
                    email=payerEmail,
                )
                invoice.finalRegistration = tr.finalize()
                invoice.save()

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

            # Send users back to the invoice to confirm the successful payment.
            # If none is specified, then return to the registration page.
            returnPage = getReturnPage(request.session.get('SITE_HISTORY', {}))
            if returnPage.get('url'):
                return HttpResponseRedirect(returnPage['url'])
            return HttpResponseRedirect(reverse('registration'))
    return HttpResponseBadRequest()

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

        sctable.append(['',]+[form.cleaned_data['j{0}'.format(jidx)] for jidx in range(0,judges)] + ['"1-{0}"'.format(p) for p in range(1,competitors+1)] + [_('Place'),])

        for cidx in range(0,competitors):
            points = [ form.cleaned_data['p{0}_{1}'.format(jidx,cidx)] for jidx in range(0,judges) ]

            places = [points.count(1),]
            for p in range(2,competitors+1):
                places.append(points.count(p)+places[-1])

            sctable.append([form.cleaned_data['c{0}'.format(cidx)],] + points + places)

        if form.cleaned_data['outType'] == '1':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="skating.csv"'

            writer = csv.writer(response, csv.excel)
            response.write(u'\ufeff'.encode('utf8'))

            for row_data in sctable: 
                writer.writerow(row_data)

            return response
        else: 
            return HttpResponseRedirect(reverse('skatingCalculator'))   
