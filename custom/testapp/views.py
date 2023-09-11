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

from .models import Competition,PrelimsRegistration,PrelimsResult,Judge
from .forms import CompetitionRegForm,PrelimsResultsForm
from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth.decorators import login_required

class CompetitionViev(ListView):
    model = Competition
    template_name = 'sc/comp_list.html'
    context_object_name = 'competitions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # Get the current user

        # Create a dict to store whether the user is a judge for each competition
        is_judge_dict = {}

        # Check if the user is a judge for each competition in the queryset
        for comp in context['competitions']:
            judges = Judge.objects.filter(comp=comp)
            is_judge = user.is_authenticated and user in [j.profile for j in judges]
            is_judge_dict[comp] = is_judge

        # Add the dict of judge status to the context
        context['is_judge_dict'] = is_judge_dict

        return context

def register_competitor(request, comp_id):
    comp = Competition.objects.get(id=comp_id)
    
    if request.method == 'POST':
        form = CompetitionRegForm(request.POST,initial={'comp': comp})
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            comp_role_id = form.cleaned_data['comp_role']
            comp_role = get_object_or_404(DanceRole, id=comp_role_id)

            comp_roles = list(comp.comp_roles.all())

            competitor, created = Customer.objects.get_or_create(first_name=first_name, last_name=last_name, email=email)

            comp_num = PrelimsRegistration.objects.filter(comp=comp,comp_role=comp_role).count() + 1
            comp_num = len(comp_roles)*comp_num-comp_roles.index(comp_role)
            try:
                prelims_reg_obj = PrelimsRegistration.objects.create(
                    competitor=competitor, comp_num=comp_num, comp=comp, comp_role=comp_role)

                competitor.save()
            
                prelims_reg_obj.save()
                return render(request, 'sc/comp_success.html', {'comp_num':comp_num})
            except IntegrityError:
                # Handle the unique constraint violation
                error_message = _("This competitor is already registered to competition.")
                return render(request, 'sc/comp_reg.html', {'form': form, 'comp': comp,'error_message':error_message})
    else:
        form = CompetitionRegForm(initial={'comp': comp})
    
    return render(request, 'sc/comp_reg.html', {'form': form, 'comp': comp})

@login_required
def submit_prelims(request, comp_id):

    comp = Competition.objects.get(id=comp_id)
    judge = Judge.objects.filter(comp=comp,profile=request.user).first()
    if not judge:
        error_message = _("Current user is not a judge for this competition.")
        return render(request, 'sc/comp_judge.html', {'comp': comp, 'error_message':error_message})

    registrations = PrelimsRegistration.objects.filter(comp=comp,comp_role=judge.prelims_role)    
    if request.method == 'POST':
        form = PrelimsResultsForm(request.POST,initial={'comp': comp,'registrations':registrations})
        if form.is_valid():
            try:
                for reg in registrations:
                    comp_res = form.cleaned_data[f'competitor_{reg.comp_num}']
                    res_obj = PrelimsResult.objects.create(comp = comp, judge = judge.profile, comp_reg=reg, result = comp_res)
                    res_obj.save()
                return redirect('prelims_results', comp_id=comp_id)
            except IntegrityError:
                # Handle the unique constraint violation
                error_message = _("This judge already submitted results.")
                return render(request, 'sc/comp_judge.html', {'form': form, 'comp': comp, 'error_message':error_message})
    else:
        form = PrelimsResultsForm(initial={'comp': comp,'registrations':registrations})

    return render(request, 'sc/comp_judge.html', {'form': form, 'comp': comp})

def prelims_results(request, comp_id):
    comp = get_object_or_404(Competition, pk=comp_id)
    judges = [j.profile for j in Judge.objects.filter(comp=comp)]

    if request.user not in judges:
        if not comp.results_visible:
            error_message = _("Prelims results are not ready yet.")
            context = {
                'error_message': error_message,
            }
            return render(request, 'sc/comp_prelims.html', context)
    
    all_results_available = True
    role_results_dict = {}
    for comp_role in comp.comp_roles.all():
        registrations = PrelimsRegistration.objects.filter(comp=comp,comp_role=comp_role).order_by('comp_role', 'comp_num')
        role_judges = [j.profile for j in Judge.objects.filter(comp=comp,prelims_role=comp_role)]
        results_dict={}
        for reg in registrations:
            results_dict[reg] = []
            for judge in role_judges:
                result = PrelimsResult.objects.filter(comp=comp, judge=judge, comp_reg=reg).first()
                if result:
                    results_dict[reg].append(result.get_result_display())
                else:
                    all_results_available = False
                    results_dict[reg].append('')
            if all_results_available:
                res_num = results_dict[reg].count('Y') + 0.5*results_dict[reg].count('Mb')
                results_dict[reg].append(res_num)

        if all_results_available:
            results_dict = dict(sorted(results_dict.items(), key=lambda item: (item[1][-1],item[1].count('Y')), reverse=True))

        role_results_dict[comp_role.pluralName] = {'judges':[j.first_name for j in role_judges],'results':results_dict}
    
        #if all_results_available:
        #    role_results_dict[comp_role.pluralName]['judges'].append('')

    context = {
        'results_dict': role_results_dict,
    }

    return render(request, 'sc/comp_prelims.html', context)