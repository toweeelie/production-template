from django.urls import path
from django.contrib import admin
from .views import MergeCustomersView,QuickCustomerRegView,SkatingCalculatorView,CompetitionViev,prelims_results,finals_results,register_competitor,submit_results

admin.autodiscover()

urlpatterns = [
    path('staff/mergecustomers/', MergeCustomersView.as_view(), name='mergeCustomers'),
    path('registrations/quickreg/', QuickCustomerRegView.as_view(), name='submitQuickreg'),
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
    path('competitions/', CompetitionViev.as_view(), name='competitions'),
    path('competitions/<int:comp_id>/register/', register_competitor, name='register_competitor'),
    path('competitions/<int:comp_id>/judging/', submit_results, name='submit_results'),
    path('competitions/<int:comp_id>/prelims/', prelims_results, name='prelims_results'),
    path('competitions/<int:comp_id>/finals/', finals_results, name='finals_results'),
]
