from django.urls import path

from brand.views import YourEndorsementsView


urlpatterns = [
    path('your-endorsements/', YourEndorsementsView.as_view(), name='your_endorsements'),
]
