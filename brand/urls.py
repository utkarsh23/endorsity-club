from django.urls import path

from brand.views import (
    YourEndorsementsView,
    ProfileView,
    QRCodeView,
    AddLocationView,
    CampaignsView,
    InitiateCampaignView,
    CampaignDetailsView,
)


urlpatterns = [
    path('your-endorsements/', YourEndorsementsView.as_view(), name='your_endorsements'),
    path('profile/', ProfileView.as_view(), name="profile"),
    path('qr-code/', QRCodeView.as_view(), name="qr_code"),
    path('add-location/', AddLocationView.as_view(), name="add_location"),
    path('campaigns/', CampaignsView.as_view(), name="campaigns"),
    path('initiate-campaign/', InitiateCampaignView.as_view(), name="initiate_campaign"),
    path('campaign/<uuid:campaign_uuid>/', CampaignDetailsView.as_view(), name="campaign_details"),
]

app_name = 'brand'
