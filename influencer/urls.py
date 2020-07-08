from django.urls import path

from influencer.views import (
    BrandsView,
    FacebookConnectView,
    FacebookVerificationView,
    FacebookVerificationFailedView,
    FacebookConfirmationView,
    AwaitVerificationView,
    ProfileView,
    QRScannerView,
    BrandUnlockView,
    PostView,
    FetchRecentIGPostsView,
    FetchIGPostThumbnailView,
)


urlpatterns = [
    path('brands/', BrandsView.as_view(), name='brands'),
    path('facebook-connect/', FacebookConnectView.as_view(), name='fb_connect'),
    path('connect/facebook/', FacebookVerificationView.as_view(), name="fb_verification"),
    path('connect/facebook/failed/', FacebookVerificationFailedView.as_view(), name='fb_failed'),
    path('connect/facebook/confirm/', FacebookConfirmationView.as_view(), name="fb_confirmation"),
    path('await-verification/', AwaitVerificationView.as_view(), name='await_verification'),
    path('profile/', ProfileView.as_view(), name="profile"),
    path('qr-scanner/', QRScannerView.as_view(), name="qr_scanner"),
    path('unlock/<uuid:brand_uuid>/', BrandUnlockView.as_view(), name="brand_unlock"),
    path('post/', PostView.as_view(), name="post"),
    path('fetch-ig-posts/', FetchRecentIGPostsView.as_view(), name="fetch_ig_posts"),
    path(
        'fetch-ig-post-thumbnail/<str:media_id>/',
        FetchIGPostThumbnailView.as_view(),
        name="fetch_ig_thumbnail"
    ),
]

app_name = 'influencer'
