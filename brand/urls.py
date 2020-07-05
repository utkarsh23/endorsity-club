from django.urls import path

from brand.views import (
    YourEndorsementsView,
    ProfileView,
    QRCodeView,
    AddLocationView,
)


urlpatterns = [
    path('your-endorsements/', YourEndorsementsView.as_view(), name='your_endorsements'),
    path('profile/', ProfileView.as_view(), name="profile"),
    path('qr-code/', QRCodeView.as_view(), name="qr_code"),
    path('add-location/', AddLocationView.as_view(), name="add_location"),
]

app_name = 'brand'
