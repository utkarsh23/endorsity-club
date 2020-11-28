import json
import requests

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from endorsity.celery import app

from accounts.models import User, Influencer, FacebookPermissions
from accounts.tokens import account_activation_token


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

@app.task
def update_ig_follower_count(user_pk):
    try:
        user = User.objects.get(pk=user_pk)
        influencer = Influencer.objects.get(user=user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        IG_USER_INFO_URI = (settings.FACEBOOK_GRAPH_URI +
            f"{fb_permissions.ig_page_id}?fields=followers_count&" +
            f"access_token={fb_permissions.user_token}")
        ig_user_info_response = json.loads(requests.get(IG_USER_INFO_URI).text)
        ig_follower_count = ig_user_info_response['followers_count']
        fb_permissions.ig_follower_count = ig_follower_count
    except:
        return
    fb_permissions.save()

@app.task
def send_activation_email(user_pk, site):
    user = User.objects.get(pk=user_pk)
    subject = f'Activate your {site.domain} account'
    message = render_to_string('accounts/activation/account_activation_email.html', {
        'user': user,
        'domain': site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'site_name': site.name,
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
