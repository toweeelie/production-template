from django.urls import path
from django.contrib import admin
from .views import MergeCustomersView,QuickCustomerRegView,SkatingCalculatorView,CompetitionViev,prelims_results,register_competitor,submit_prelims

admin.autodiscover()

urlpatterns = [
    path('staff/mergecustomers/', MergeCustomersView.as_view(), name='mergeCustomers'),
    path('registrations/quickreg/', QuickCustomerRegView.as_view(), name='submitQuickreg'),
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
    path('competitions/', CompetitionViev.as_view(), name='competitions'),
    path('competitions/<int:comp_id>/register/', register_competitor, name='register_competitor'),
    path('competitions/<int:comp_id>/judging/', submit_prelims, name='submit_prelims'),
    path('competitions/<int:comp_id>/prelims/', prelims_results, name='prelims_results'),
]
