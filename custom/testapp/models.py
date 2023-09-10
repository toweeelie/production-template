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
    comp_roles = models.ManyToManyField(
        DanceRole, verbose_name=_('Dance roles'),
    )
    pair_finalists = models.BooleanField(
        _('Paired Final'), default=True, blank=True
    )
    results_visible = models.BooleanField(
        _('Publish results'), default=False, blank=False
    )

class Judge(models.Model):
    '''
    Judge model
    '''
    profile = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    comp = models.ForeignKey(
        Competition, on_delete=models.CASCADE
    )
    prelims = models.BooleanField(
        _('Judging Prelims'), default=False
    )
    finals = models.BooleanField(
        _('Judging Finals'), default=False
    )
    prelims_role = models.ForeignKey(
        DanceRole, on_delete=models.CASCADE
    )
    class Meta:
        unique_together = ('profile', 'comp')

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

class PrelimsResult(models.Model):
    '''
    Prelims results
    '''
    JUDGE_CHOICES = (
        ('yes', 'Y'),
        ('maybe', 'Mb'),
        ('no', ''),
    )

    comp = models.ForeignKey(Competition, on_delete=models.CASCADE)
    judge = models.ForeignKey(User, on_delete=models.CASCADE)
    comp_reg = models.ForeignKey(PrelimsRegistration, on_delete=models.CASCADE)
    result = models.CharField(max_length=10, choices=JUDGE_CHOICES, default='no')

    class Meta:
        unique_together = ('comp', 'judge', 'comp_reg')