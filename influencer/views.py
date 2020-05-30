import json
import requests

from django.conf import settings
from django.views.generic.base import TemplateView, View
from django.shortcuts import render, redirect

from accounts.models import (
    FacebookPermissions,
    Influencer,
)

from influencer.mixins import (
    NotFbConnectedInfluencerLoginRequiredMixin,
    NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin,
    VerifiedAndFbConnectedInfluencerLoginRequiredMixin,
)


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
        permissions_string = '%2C'.join(permissions)
        print(permissions_string)
        code = request.GET.get('code', '')
        if code == '':
            state = "storeInitialState"
            AUTH_URI = (settings.FACEBOOK_AUTH_URL +
                f'client_id={settings.FACEBOOK_KEY}' +
                f'&redirect_uri={settings.FACEBOOK_REDIRECT_URI}' +
                f'&state={state}' +
                f'&scope={permissions_string}')
            return redirect(AUTH_URI)
        return HttpResponseRedirect('/influencer/verify/failed/')


class FacebookConfirmationView(NotFbConnectedInfluencerLoginRequiredMixin, View):

    def get(self, request):
        code = request.GET.get('code', '')
        ACCESS_TOKEN_URI = (settings.FACEBOOK_REQUEST_ACCESS_URL +
            f'client_id={settings.FACEBOOK_KEY}' +
            f'&redirect_uri={settings.FACEBOOK_REDIRECT_URI}' +
            f'&client_secret={settings.FACEBOOK_SECRET}' +
            f'&code={code}')
        try:
            access_token_response = json.loads(requests.get(ACCESS_TOKEN_URI).text)
            token = access_token_response['access_token']
        except:
            return HttpResponseRedirect('/influencer/verify/failed/')

        # PAGE_ID_AND_TOKEN_URI = (settings.FACEBOOK_GRAPH_URI +
        #     "me/accounts?" +
        #     "" +
        #     f"access_token={token}")
        # try:
        #     page_id_and_token_response = json.loads(requests.get(PAGE_ID_AND_TOKEN_URI).text)
        #     print(page_id_and_token_response)
        #     page_id = page_id_and_token_response['data'][0]['id']
        #     page_token = page_id_and_token_response['data'][0]['access_token']
        # except:
        #     pass

        # PAGE_FAN_COUNT_URI = (settings.FACEBOOK_GRAPH_URI +
        #     f"{page_id}?fields=instagram_business_account&" +
        #     f"access_token={token}") # +
        #     # "&fields=fan_count,name")
        # try:
        #     page_fan_count_response = json.loads(requests.get(PAGE_FAN_COUNT_URI).text)
        #     print(page_fan_count_response)
        #     insta_page_id = page_fan_count_response['instagram_business_account']['id']
        # except:
        #     pass
        
        # URI = (settings.FACEBOOK_GRAPH_URI +
        #     f"{insta_page_id}/media?" +
        #     f"access_token={token}")
        # page_fan_count_response = json.loads(requests.get(URI).text)['data']
        # print(page_fan_count_response)
        # for idd in page_fan_count_response:
        #     URL = (settings.FACEBOOK_GRAPH_URI +
        #     f"{idd['id']}/" +
        #     "insights?metric=engagement,impressions,reach&" +
        #     f"access_token={token}")
        #     print(json.loads(requests.get(URL).text))
        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        my_id = json.loads(requests.get(settings.FACEBOOK_GRAPH_URI + f'me?access_token={token}').text)['id']
        permissions_URL = settings.FACEBOOK_GRAPH_URI + f'{my_id}/permissions?access_token={token}'
        check_permissions = json.loads(requests.get(permissions_URL).text)
        for permissionobj in check_permissions['data']:
            if permissionobj['status'] == 'granted':
                if permissionobj['permission'] == 'instagram_basic':
                    fb_permissions.instagram_basic = True
                elif permissionobj['permission'] == 'instagram_manage_insights':
                    fb_permissions.instagram_manage_insights = True
                elif permissionobj['permission'] == 'pages_read_engagement':
                    fb_permissions.pages_read_engagement = True
                fb_permissions.save()
        return redirect('/')

        # if likes_count > settings.FACEBOOK_LIKES_THRESHOLD:
        #     influencer = Influencer.objects.get(user=request.user)
        #     influencer.fb_verified = True
        #     influencer.fb_likes_count = likes_count
        #     influencer.fb_page_id = page_id
        #     influencer.fb_last_updated = datetime.datetime.now()
        #     influencer.save()
        #     return HttpResponseRedirect('/influencer/verify/success/')
        # else:
        #     return HttpResponseRedirect('/influencer/verify/failed/')


class AwaitVerificationView(NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/await_verification.html'


class BrandsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/brands.html'
