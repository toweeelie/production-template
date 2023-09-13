from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from danceschool.core.admin import CustomerAdmin

from .models import Competition,Judge,PrelimsRegistration,PrelimsResult,FinalsResult

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
    extra = 0

    def get_queryset(self, request):
        # Get the parent Competition object from the request's URL parameters
        competition_id = request.resolver_match.kwargs.get('object_id')
        competition = Competition.objects.get(pk=competition_id)

        # Customize the queryset based on the stage attribute of the Competition object
        queryset = super().get_queryset(request)

        if competition.stage in ['d','f']:
            queryset = queryset.filter(finalist=True, comp_role=competition.comp_roles.first())

        return queryset
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'final_partner':
            # Get the parent Competition object from the request's URL parameters
            competition_id = request.resolver_match.kwargs.get('object_id')
            competition = Competition.objects.get(pk=competition_id)

            # Customize the queryset for the final_partner field
            kwargs['queryset'] = PrelimsRegistration.objects.filter(
                comp_role=competition.comp_roles.last(),
                finalist=True
            ).exclude(pk=competition.pk)  # Exclude the current registration

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class JudgeInline(admin.TabularInline):
    model = Judge
    extra = 0

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title','results_visible')
    inlines = [JudgeInline,PrelimsRegistrationInline]

@admin.register(PrelimsResult)
class PrelimsResultAdmin(admin.ModelAdmin):
    list_display = ('comp', 'judge', 'comp_reg','result') 
    list_filter = ('comp','judge',)

@admin.register(FinalsResult)
class FinalsResultAdmin(admin.ModelAdmin):
    list_display = ('comp', 'judge', 'comp_reg','result') 
    list_filter = ('comp','judge',)
