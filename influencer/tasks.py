import datetime
import dateutil.parser
import json
import requests

from django.conf import settings

from accounts.models import (
    FacebookPermissions,
    Influencer,
    User,
)

from endorsity.celery import app

from influencer.models import InfluencerStatistics


@app.task
def update_influencer_statistics(user_pk):
    user = User.objects.get(pk=user_pk)
    influencer = Influencer.objects.get(user=user)
    fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
    influencer_statistics = InfluencerStatistics.objects.filter(influencer=influencer).first()
    if not influencer_statistics:
        influencer_statistics = InfluencerStatistics(influencer=influencer)

    # audience_city & audience_gender_age
    LIFETIME_STATS_URI = (settings.FACEBOOK_GRAPH_URI +
        f"{fb_permissions.ig_page_id}/insights?" +
        "metric=audience_city%2Caudience_gender_age&" +
        "period=lifetime&" +
        f"access_token={fb_permissions.user_token}")
    lifetime_stats_response = json.loads(requests.get(LIFETIME_STATS_URI).text)
    audience_city = []
    audience_gender_age = []
    for city, stat in lifetime_stats_response['data'][0]['values'][0]['value'].items():
        audience_city.append([city, str(stat)])
    for gender_age, stat in lifetime_stats_response['data'][1]['values'][0]['value'].items():
        audience_gender_age.append([gender_age, str(stat)])
    influencer_statistics.audience_city = audience_city
    influencer_statistics.audience_gender_age = audience_gender_age

    # impressions & follower_counts
    PROLONGED_URI = (settings.FACEBOOK_GRAPH_URI +
        f"{fb_permissions.ig_page_id}/insights?" +
        "metric=impressions%2Cfollower_count&" +
        "period=day&limit=100&" +
        f"access_token={fb_permissions.user_token}")
    now_timestamp = datetime.datetime.now()
    impressions = []
    follower_counts = []
    for period in range(12):
        since = str((now_timestamp - datetime.timedelta(days=(30 * (period + 1)))).timestamp()).split('.')[0]
        until = str((now_timestamp - datetime.timedelta(days=(30 * period))).timestamp()).split('.')[0]
        PERIOD_PROLONGED_URI = PROLONGED_URI + f"&since={since}&until={until}"
        period_prolonged_response = json.loads(requests.get(PERIOD_PROLONGED_URI).text)
        for impression in reversed(period_prolonged_response['data'][0]['values']):
            impressions.append(
                [
                    str(dateutil.parser.parse(impression['end_time']).timestamp()).split('.')[0],
                    str(impression['value']),
                ]
            )
        for follower_count in reversed(period_prolonged_response['data'][1]['values']):
            follower_counts.append(
                [
                    str(dateutil.parser.parse(follower_count['end_time']).timestamp()).split('.')[0],
                    str(follower_count['value']),
                ]
            )
    influencer_statistics.impressions = impressions
    influencer_statistics.follower_counts = follower_counts
    influencer_statistics.save()
