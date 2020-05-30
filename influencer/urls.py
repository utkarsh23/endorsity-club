from django.urls import path

from influencer.views import (
    BrandsView,
    FacebookConnectView,
    FacebookVerificationView,
    FacebookConfirmationView,
    AwaitVerificationView,
)


urlpatterns = [
    path('brands/', BrandsView.as_view(), name='brands'),
    path('facebook-connect/', FacebookConnectView.as_view(), name='fb_connect'),
    path('connect/facebook/', FacebookVerificationView.as_view(), name="fb_verification"),
    path('connect/facebook/confirm/', FacebookConfirmationView.as_view(), name="fb_confirmation"),
    path('await-verification/', AwaitVerificationView.as_view(), name='await_verification')
]

app_name = 'influencer'
