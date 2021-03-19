from django.urls import path
from django.contrib import admin
from .views import MergeCustomersView,handle_quickreg,SkatingCalculatorView 

admin.autodiscover()

urlpatterns = [
    path('staff/mergecustomers/', MergeCustomersView.as_view(), name='mergeCustomers'),
    path('registrations/quickreg/', handle_quickreg, name='submitQuickreg'),
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
]
