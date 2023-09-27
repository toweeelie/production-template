from django.urls import path
from django.contrib import admin
from .views import MergeCustomersView,QuickCustomerRegView,SCRedirectView

admin.autodiscover()

urlpatterns = [
    path('staff/mergecustomers/', MergeCustomersView.as_view(), name='mergeCustomers'),
    path('registrations/quickreg/', QuickCustomerRegView.as_view(), name='submitQuickreg'),
    path('skatingcalculator/', SCRedirectView.as_view(), name='scRedirect'),
]
