from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from danceschool.core.admin import CustomerAdmin
from django.core.exceptions import ObjectDoesNotExist

def mergeCustomers(self, request, queryset):
    # Allows use of the email view to contact specific customers.
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(reverse('mergeCustomers') + "?customers=%s" % (
        ", ".join(selected)
    ))
mergeCustomers.short_description = _('Merge selected customers')

CustomerAdmin.actions.append(mergeCustomers)
