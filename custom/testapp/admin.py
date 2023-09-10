from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from danceschool.core.admin import CustomerAdmin

from .models import Competition,PrelimsRegistration,Judge

def mergeCustomers(self, request, queryset):
    # Allows use of the email view to contact specific customers.
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(reverse('mergeCustomers') + "?customers=%s" % (
        ", ".join(selected)
    ))
mergeCustomers.short_description = _('Merge selected customers')

CustomerAdmin.actions.append(mergeCustomers)


class PrelimsRegistrationInline(admin.TabularInline):
    model = PrelimsRegistration
    extra = 1

class JudgeInline(admin.TabularInline):
    model = Judge
    extra = 1

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title','results_visible')
    inlines = [JudgeInline,PrelimsRegistrationInline]

@admin.register(PrelimsRegistration)
class PrelimsRegistrationAdmin(admin.ModelAdmin):
    list_display = ('comp', 'comp_num', 'competitor', 'comp_role','comp_checked_in')  # Add other fields to display in the list view
    list_filter = ('comp',)  # Add fields to filter the list view
    search_fields = ('comp_num', 'competitor__first_name', 'competitor__last_name', 'competitor__email')  # Add fields to search in the list view
