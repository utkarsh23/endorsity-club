from django.urls import path

from accounts.models import Brand

from influencer.serializers import brands_view_serializer
from influencer.views import (
    BrandsView,
    FacebookConnectView,
    FacebookVerificationView,
    FacebookVerificationFailedView,
    FacebookConfirmationView,
    AwaitVerificationView,
    ProfileAnalyticsView,
    ProfileEndorsementsView,
    ProfileBadgeView,
    QRScannerView,
    BrandUnlockView,
    PostView,
    FetchRecentIGPostsView,
    FetchIGPostThumbnailView,
    FetchBrandsInfiniteAPIView,
    BrandProfileView,
    FetchInstaEmbedPost,
)


urlpatterns = [
    path('brands/', BrandsView.as_view(), name='brands'),
    path('facebook-connect/', FacebookConnectView.as_view(), name='fb_connect'),
    path('connect/facebook/', FacebookVerificationView.as_view(), name="fb_verification"),
    path('connect/facebook/failed/', FacebookVerificationFailedView.as_view(), name='fb_failed'),
    path('connect/facebook/confirm/', FacebookConfirmationView.as_view(), name="fb_confirmation"),
    path('await-verification/', AwaitVerificationView.as_view(), name='await_verification'),
    path('profile/analytics/', ProfileAnalyticsView.as_view(), name="profile_analytics"),
    path('profile/endorsements/', ProfileEndorsementsView.as_view(), name="profile_endorsements"),
    path('profile/badge/', ProfileBadgeView.as_view(), name="profile_badge"),
    path('qr-scanner/', QRScannerView.as_view(), name="qr_scanner"),
    path('unlock/<uuid:brand_uuid>/', BrandUnlockView.as_view(), name="brand_unlock"),
    path('post/', PostView.as_view(), name="post"),
    path('fetch-ig-posts/', FetchRecentIGPostsView.as_view(), name="fetch_ig_posts"),
    path('fetch-insta-html/<insta_url_encoded>/', FetchInstaEmbedPost.as_view(), name="inf_insta_html"),
    path(
        'fetch-ig-post-thumbnail/<str:media_id>/',
        FetchIGPostThumbnailView.as_view(),
        name="fetch_ig_thumbnail"
    ),
    path(
        'fetch-brands/<int:page_no>/',
        FetchBrandsInfiniteAPIView.as_view(),
        kwargs={
            'initial_count': 10,
            'paginator_count': 5,
            'db_model': Brand,
            'filters': {
                'is_subscription_active': True,
            },
            'order_by': [],
            'custom_serializer': brands_view_serializer,
        },
        name="fetch_brands",
    ),
    path('brand/<uuid:brand_uuid>/', BrandProfileView.as_view(), name="brand_profile"),
]

app_name = 'influencer'
