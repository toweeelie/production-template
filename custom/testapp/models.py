from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from danceschool.core.models import Customer,DanceRole

    


class Competition(models.Model):
    '''
    Competition model
    '''

    title = models.CharField(
        _('Competition name'),
        max_length=200,
    )

    judjes = models.ManyToManyField(
        User, verbose_name=_('Judjes'),
    )

    comp_roles = models.ManyToManyField(
        DanceRole, verbose_name=_('Dance roles'),
    )

    pairFinalists = models.BooleanField(
        _('Paired Final'), default=True, blank=True
    )

    resultsVisible = models.BooleanField(
        _('Publish results'), default=False, blank=False
    )

class PrelimsRegistration(models.Model):
    '''
    Prelims registration record
    '''
    comp = models.ForeignKey(
        Competition, on_delete=models.CASCADE
    )
    comp_num = models.IntegerField()
    competitor = models.ForeignKey(
        Customer, verbose_name=_('Competitor'), on_delete=models.CASCADE,
    )
    comp_role = models.ForeignKey(
        DanceRole, verbose_name=_('Dance Role'), on_delete=models.CASCADE,
    )
    comp_checked_in = models.BooleanField(
        _('Checked In'), default=False, blank=False
    )

    class Meta:
        unique_together = ('comp', 'competitor')