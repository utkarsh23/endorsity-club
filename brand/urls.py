from django.urls import path

from accounts.models import Influencer

from brand.serializers import influencers_view_serializer
from brand.views import (
    ProfileView,
    QRCodeView,
    AddLocationView,
    CampaignsView,
    InitiateCampaignView,
    InfluencersView,
    InfluencerAnalyticsView,
    InfluencerEndorsementsView,
    InfluencerBadgeView,
    FetchInfluencersInfiniteAPIView,
    EditActiveLocationsView,
)


urlpatterns = [
    path('profile/', ProfileView.as_view(), name="profile"),
    path('qr-code/', QRCodeView.as_view(), name="qr_code"),
    path('add-location/', AddLocationView.as_view(), name="add_location"),
    path('campaign/', CampaignsView.as_view(), name="campaign"),
    path('initiate-campaign/', InitiateCampaignView.as_view(), name="initiate_campaign"),
    path('influencers/', InfluencersView.as_view(), name="influencers"),
    path('influencer/<str:influencer_pk>/analytics/', InfluencerAnalyticsView.as_view(), name="influencer_analytics"),
    path('influencer/<str:influencer_pk>/endorsements/', InfluencerEndorsementsView.as_view(), name="influencer_endorsements"),
    path('influencer/<str:influencer_pk>/badge/', InfluencerBadgeView.as_view(), name="influencer_badge"),
    path(
        'fetch-influencers/<int:page_no>/',
        FetchInfluencersInfiniteAPIView.as_view(),
        kwargs={
            'initial_count': 10,
            'paginator_count': 5,
            'db_model': Influencer,
            'filters': {
                'is_verified': True,
            },
            'order_by': [],
            'custom_serializer': influencers_view_serializer,
        },
        name="fetch_influencers",
    ),
    path('edit-active-locations/', EditActiveLocationsView.as_view(), name='edit_active_locations'),
]

app_name = 'brand'
