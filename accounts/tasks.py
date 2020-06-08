import json
import requests

from django.conf import settings

from endorsity.celery import app

from accounts.models import User, Influencer, FacebookPermissions


@app.task
def email_message_async(email_message):
    email_message.send()

@app.task
def update_fb_user_token(user_pk):
    try:
        user = User.objects.get(pk=user_pk)
        influencer = Influencer.objects.get(user=user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        LONG_ACCESS_TOKEN_URI = (settings.FACEBOOK_REQUEST_ACCESS_URL +
            "grant_type=fb_exchange_token" +
            f'&client_id={settings.FACEBOOK_KEY}' +
            f'&client_secret={settings.FACEBOOK_SECRET}' +
            f"&fb_exchange_token={fb_permissions.user_token}")
        long_access_token_response = json.loads(requests.get(LONG_ACCESS_TOKEN_URI).text)
        long_lived_token = long_access_token_response['access_token']
        fb_permissions.user_token = long_lived_token
    except:
        return
    fb_permissions.save()