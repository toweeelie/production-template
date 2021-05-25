from django.urls import path
from django.contrib import admin
from .views import MergeCustomersView,QuickCustomerRegView,SkatingCalculatorView 

admin.autodiscover()

urlpatterns = [
    path('staff/mergecustomers/', MergeCustomersView.as_view(), name='mergeCustomers'),
    path('registrations/quickreg/', QuickCustomerRegView.as_view(), name='submitQuickreg'),
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
]
