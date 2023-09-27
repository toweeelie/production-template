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
from .forms import QuickCustomerRegForm, MergeCustomersForm

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
        occurrence = form.cleaned_data.get('eventOccurrence')
        expiry = timezone.now() + timedelta(minutes=getConstant('registration__sessionExpiryMinutes'))

        reg = Registration(
                submissionUser=subUser, dateTime=timezone.now(),
                payAtDoor=True,
            )

        invoice = reg.link_invoice(expirationDate=expiry)
        reg.save()

        tr = EventRegistration(
                customer=customer, event=event, 
                dropIn=dropIn, role_id=role,
            )

        if dropIn:
            dropInList = [occurrence.id]
            tr.data['__dropInOccurrences'] = dropInList
            price = event.getBasePrice(dropIns=len(dropInList))
        else:
            price = event.getBasePrice(payAtDoor=reg.payAtDoor)

        tr.registration = reg
        tr.save(grossTotal=price, total=price)

        if payLater == True:
            invoice.status = Invoice.PaymentStatus.unpaid
            invoice.save()
            invoice.registration.finalize()
        else:
            paymentMethod = form.cleaned_data.get('paymentMethod','Cash')
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

        return HttpResponseRedirect(reverse('viewregistrations',
                                            kwargs={'event_id':event.id}))

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
