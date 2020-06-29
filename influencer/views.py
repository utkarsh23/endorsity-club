import hashlib
import json
import os
import requests

from django.conf import settings
from django.db.models import Q
from django.views.generic.base import TemplateView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from accounts.models import (
    FacebookPermissions,
    Influencer,
)

from influencer.mixins import (
    NotFbConnectedInfluencerLoginRequiredMixin,
    NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin,
    VerifiedAndFbConnectedInfluencerLoginRequiredMixin,
)

from notifications.models import Notification


class FacebookConnectView(NotFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/facebook_connect.html'


class FacebookVerificationView(NotFbConnectedInfluencerLoginRequiredMixin, View):

    def get(self, request):
        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        permissions = []
        if not fb_permissions.pages_read_engagement:
            permissions.append('pages_read_engagement')
        if not fb_permissions.instagram_basic:
            permissions.append('instagram_basic')
        if not fb_permissions.instagram_manage_insights:
            permissions.append('instagram_manage_insights')
        if not fb_permissions.pages_show_list:
            permissions.append('pages_show_list')
        permissions_string = '%2C'.join(permissions)
        # https://developers.google.com/identity/protocols/oauth2/openid-connect?hl=fr#python
        # handle state by saving random state in session state variable & checking in the view
        # FacebookConfirmationView if the returned state matches the session state
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        request.session['state'] = state
        AUTH_URI = (settings.FACEBOOK_AUTH_URL +
            f'client_id={settings.FACEBOOK_KEY}' +
            f'&redirect_uri={settings.FACEBOOK_REDIRECT_URI}' +
            f'&state={state}' +
            f'&scope={permissions_string}')
        return redirect(AUTH_URI)


class FacebookVerificationFailedView(NotFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/facebook_failed.html'


class FacebookConfirmationView(NotFbConnectedInfluencerLoginRequiredMixin, View):

    def get(self, request):
        code = request.GET.get('code', '')
        if request.GET.get('error', '') != '' or \
            request.GET.get('state') != request.session['state'] or \
            code == '':
            return redirect(reverse_lazy('influencer:fb_failed'))

        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)

        try:
            # get short lived user access token
            ACCESS_TOKEN_URI = (settings.FACEBOOK_REQUEST_ACCESS_URL +
                f'client_id={settings.FACEBOOK_KEY}' +
                f'&redirect_uri={settings.FACEBOOK_REDIRECT_URI}' +
                f'&client_secret={settings.FACEBOOK_SECRET}' +
                f'&code={request.GET.get("code")}')
            access_token_response = json.loads(requests.get(ACCESS_TOKEN_URI).text)
            token = access_token_response['access_token']

            # get long lived user access token
            LONG_ACCESS_TOKEN_URI = (settings.FACEBOOK_REQUEST_ACCESS_URL +
                "grant_type=fb_exchange_token" +
                f'&client_id={settings.FACEBOOK_KEY}' +
                f'&client_secret={settings.FACEBOOK_SECRET}' +
                f"&fb_exchange_token={token}")
            long_access_token_response = json.loads(requests.get(LONG_ACCESS_TOKEN_URI).text)
            long_lived_token = long_access_token_response['access_token']
            fb_permissions.user_token = long_lived_token

            # find user id
            user_id = json.loads(requests.get(settings.FACEBOOK_GRAPH_URI +
                f'me?access_token={token}').text)['id']
            fb_permissions.user_id = user_id

            # check for facebook permissions
            PERMISSIONS_URL = (settings.FACEBOOK_GRAPH_URI +
                f'{user_id}/permissions?access_token={long_lived_token}')
            check_permissions = json.loads(requests.get(PERMISSIONS_URL).text)
            for permissionobj in check_permissions['data']:
                if permissionobj['status'] == 'granted':
                    if permissionobj['permission'] == 'instagram_basic':
                        fb_permissions.instagram_basic = True
                    elif permissionobj['permission'] == 'instagram_manage_insights':
                        fb_permissions.instagram_manage_insights = True
                    elif permissionobj['permission'] == 'pages_read_engagement':
                        fb_permissions.pages_read_engagement = True
                    elif permissionobj['permission'] == 'pages_show_list':
                        fb_permissions.pages_show_list = True

            # fb page id
            FB_PAGE_ID_URI = (settings.FACEBOOK_GRAPH_URI +
                "me/accounts?" +
                f"access_token={long_lived_token}")
            fb_page_id_response = json.loads(requests.get(FB_PAGE_ID_URI).text)
            fb_page_id = fb_page_id_response['data'][0]['id']
            fb_permissions.fb_page_id = fb_page_id

            # ig page id
            IG_PAGE_ID_URI = (settings.FACEBOOK_GRAPH_URI +
                f"{fb_page_id}?fields=instagram_business_account&" +
                f"access_token={long_lived_token}")
            ig_page_id_response = json.loads(requests.get(IG_PAGE_ID_URI).text)
            ig_page_id = ig_page_id_response['instagram_business_account']['id']
            fb_permissions.ig_page_id = ig_page_id
        except:
            return redirect(reverse_lazy('influencer:fb_failed'))

        fb_permissions.save()

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.DAYS,
        )
        current_task = PeriodicTask.objects.filter(
            name=f'Influencer {fb_permissions.influencer.user.pk} Update User Token'
        )
        if current_task.exists():
            current_task.delete()
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'Influencer {fb_permissions.influencer.user.pk} Update User Token',
            task='accounts.tasks.update_fb_user_token',
            args=json.dumps([fb_permissions.influencer.user.pk,]),
        )
        return redirect(reverse_lazy('accounts:landing'))


class AwaitVerificationView(NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/await_verification.html'


class BrandsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/brands.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notifications'] = (Notification.objects
            .filter(user=self.request.user)
            .order_by('-created_at'))[:8]
        context['notifs_unread'] = (Notification.objects
            .filter(Q(user=self.request.user) & Q(is_seen=False)).count())
        return context
