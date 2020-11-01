import datetime
import hashlib
import json
import os
import requests

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from accounts.mixins import RegisteredLoginRequiredMixin
from accounts.models import (
    Brand,
    FacebookPermissions,
    Influencer,
    Location,
    get_profile_picture_path,
)
from accounts.utils import (
    center_crop_and_square_image,
    resize_image,
)
from accounts.views import InfiniteAPIView

from brand.models import Campaign

from influencer.forms import LocationSelectForm, PostSelectForm
from influencer.mixins import (
    NotFbConnectedInfluencerLoginRequiredMixin,
    NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin,
    VerifiedAndFbConnectedInfluencerLoginRequiredMixin,
)
from influencer.models import InfluencerStatistics, EndorsingPost
from influencer.tasks import (
    delete_update_post_stats,
    update_influencer_statistics,
    update_post_stats,
)

from notifications.models import Notification
from notifications.utils import create_and_broadcast_notification


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

            # ig username
            IG_USER_INFO_URI = (settings.FACEBOOK_GRAPH_URI +
                f"{ig_page_id}?" +
                "fields=username%2Cfollowers_count%2Cprofile_picture_url&" +
                f"access_token={long_lived_token}")
            ig_user_info_response = json.loads(requests.get(IG_USER_INFO_URI).text)
            ig_username = ig_user_info_response['username']
            ig_follower_count = ig_user_info_response['followers_count']
            fb_permissions.ig_username = ig_username
            fb_permissions.ig_follower_count = ig_follower_count

            # save instagram profile picture
            image = requests.get(ig_user_info_response['profile_picture_url'])
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(image.content)
            img_temp.flush()
            fb_permissions.influencer.user.profile_picture.save(os.path.join(
                settings.BASE_DIR, get_profile_picture_path(fb_permissions.influencer.user, 'filename')),
                File(img_temp)
            )
            center_crop_and_square_image(os.path.join(
                settings.BASE_DIR, fb_permissions.influencer.user.profile_picture.url[1:]))
            resize_image(os.path.join(
                settings.BASE_DIR, fb_permissions.influencer.user.profile_picture.url[1:]))
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

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=3,
            period=IntervalSchedule.HOURS,
        )
        current_task = PeriodicTask.objects.filter(
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Follower Count'
        )
        if current_task.exists():
            current_task.delete()
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Follower Count',
            task='accounts.tasks.update_ig_follower_count',
            args=json.dumps([fb_permissions.influencer.user.pk,]),
        )

        update_influencer_statistics.delay(fb_permissions.influencer.user.pk)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        current_task = PeriodicTask.objects.filter(
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Influencer Statistics'
        )
        if current_task.exists():
            current_task.delete()
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Influencer Statistics',
            task='influencer.tasks.update_influencer_statistics',
            args=json.dumps([fb_permissions.influencer.user.pk,]),
        )
        return redirect(reverse_lazy('accounts:landing'))


class AwaitVerificationView(NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/await_verification.html'


class BrandsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/brands.html'


class ProfileAnalyticsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=Influencer.objects.get(user=self.request.user)))
        influencer_statistics = (InfluencerStatistics.objects
            .get(influencer=Influencer.objects.get(user=self.request.user)))
        if influencer_statistics.audience_city:
            context['audience_city_stats'] = sorted(
                influencer_statistics.audience_city,
                reverse=True,
                key=lambda el: int(el[1]))[:3]
        if influencer_statistics.audience_gender_age:
            context['audience_demographic'] = [
                [el[0].replace('M.', 'Male ').replace('F.', 'Female ').replace('U.', 'Unknown '), int(el[1])]
                for el in influencer_statistics.audience_gender_age]
        if influencer_statistics.impressions:
            context['impressions'] = [
                [datetime.datetime.utcfromtimestamp(int(el[0])).strftime('%d %b %y'), int(el[1])]
                for el in influencer_statistics.impressions[::-1]]
        if influencer_statistics.follower_counts:
            context['follower_counts'] = [
                [datetime.datetime.utcfromtimestamp(int(el[0])).strftime('%d %b %y'), int(el[1])]
                for el in influencer_statistics.follower_counts[::-1]]
        context['base_template'] = 'influencer/base.html'
        return context


class ProfileEndorsementsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_endorsements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=Influencer.objects.get(user=self.request.user)))
        context['endorsements'] = (EndorsingPost.objects
            .filter(influencer=Influencer.objects.get(user=self.request.user), complete=True).order_by('-created_at'))
        context['base_template'] = 'influencer/base.html'
        return context


class ProfileBadgeView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_badge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=Influencer.objects.get(user=self.request.user)))
        context['base_template'] = 'influencer/base.html'
        return context


class QRScannerView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'influencer/qr_scanner.html'


class BrandUnlockView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, FormView):
    template_name = 'influencer/brand_unlock.html'
    form_class = LocationSelectForm
    success_url = reverse_lazy('influencer:post')

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), brand_uuid=self.kwargs['brand_uuid'])

    def form_valid(self, form):
        if (Influencer.objects.get(user=self.request.user).is_unlocked):
            return redirect(reverse_lazy('influencer:post'))
        location_uuid = form.cleaned_data['location']
        location = Location.objects.get(id=location_uuid)
        if not location.brand.is_subscription_active:
            return super().form_invalid(form)
        campaign = (Campaign.objects.filter(brand=location.brand)
                    .order_by('-start_time').first())
        influencer = Influencer.objects.get(user=self.request.user)
        endorsing_post = EndorsingPost.objects.create(
            influencer=influencer,
            campaign=campaign,
            location=location,
        )
        influencer.is_unlocked = True
        influencer.save()
        return super().form_valid(form)


class PostView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, FormView):
    template_name = 'influencer/post.html'
    form_class = PostSelectForm
    success_url = reverse_lazy('influencer:profile_endorsements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        influencer = Influencer.objects.get(user=self.request.user)
        if influencer.is_unlocked:
            context['post'] = (EndorsingPost.objects
                                .get(influencer__user=self.request.user, complete=False))
        return context

    def form_valid(self, form):
        media_id = form.cleaned_data['media_id']
        influencer = Influencer.objects.get(user=self.request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        IG_MEDIA_LINK = (settings.FACEBOOK_GRAPH_URI +
            f"{media_id}?" +
            "fields=permalink%2Cmedia_type&"+
            f"access_token={fb_permissions.user_token}")
        ig_media_link_response = json.loads(requests.get(IG_MEDIA_LINK).text)
        post = (EndorsingPost.objects
                .get(influencer=influencer, complete=False))
        post.complete = True
        post.media_id = media_id
        post.media_type = ig_media_link_response['media_type']
        post.media_embed_url = ig_media_link_response['permalink']
        post.save()
        influencer.is_unlocked = False
        influencer.save()

        update_post_stats.delay(post.id)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=2,
            period=IntervalSchedule.HOURS,
        )
        current_task = PeriodicTask.objects.filter(
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Post {post.id} Statistics'
        )
        if current_task.exists():
            current_task.delete()
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'Influencer {fb_permissions.influencer.user.pk} Update Post {post.id} Statistics',
            task='influencer.tasks.update_post_stats',
            args=json.dumps([str(post.id)]),
        )
        stop_update_time = datetime.datetime.now() + datetime.timedelta(days=30, minutes=30)
        delete_update_post_stats.apply_async((fb_permissions.influencer.user.pk, post.id), eta=stop_update_time)
        message = f"You have a new endorsement from {fb_permissions.ig_username}!"
        link = f"/brand/influencer/{urlsafe_base64_encode(force_bytes(influencer.user.pk))}/endorsements/"
        create_and_broadcast_notification(post.campaign.brand.user.pk, message, link)
        return super().form_valid(form)


class FetchRecentIGPostsView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, View):

    def get(self, request):
        influencer = Influencer.objects.get(user=self.request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        IG_MEDIA = (settings.FACEBOOK_GRAPH_URI +
            f"{fb_permissions.ig_page_id}?" +
            "limit=25&fields=media&"+
            f"access_token={fb_permissions.user_token}")
        ig_media_response = json.loads(requests.get(IG_MEDIA).text)
        return JsonResponse(ig_media_response)


class FetchIGPostThumbnailView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, View):

    def get(self, request, media_id):
        influencer = Influencer.objects.get(user=self.request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        IG_MEDIA_LINK = (settings.FACEBOOK_GRAPH_URI +
            f"{media_id}?" +
            "fields=media_url%2Cmedia_type%2Cid&"+
            f"access_token={fb_permissions.user_token}")
        ig_media_link_response = json.loads(requests.get(IG_MEDIA_LINK).text)
        if ig_media_link_response['media_type'] == 'VIDEO':
            IG_MEDIA_LINK = (settings.FACEBOOK_GRAPH_URI +
                f"{media_id}?" +
                "fields=thumbnail_url%2Cid&"+
                f"access_token={fb_permissions.user_token}")
            ig_media_link_response = json.loads(requests.get(IG_MEDIA_LINK).text)
            response = {
                "link": ig_media_link_response["thumbnail_url"],
                "id": ig_media_link_response["id"],
            }
        else:
            response = {
                "link": ig_media_link_response["media_url"],
                "id": ig_media_link_response["id"],
            }
        return JsonResponse(response)


class FetchBrandsInfiniteAPIView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, InfiniteAPIView):
    pass


class BrandProfileView(VerifiedAndFbConnectedInfluencerLoginRequiredMixin, TemplateView):
    template_name = 'brand/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(id=kwargs['brand_uuid'])
        context['base_template'] = 'influencer/base.html'
        context['brand'] = brand
        context['locations'] = Location.objects.filter(brand=brand, active=True)
        context['endorsements'] = (EndorsingPost.objects
            .filter(campaign__brand__user=brand.user, complete=True).order_by('-created_at'))
        return context

class FetchInstaEmbedPost(RegisteredLoginRequiredMixin, View):

    def get(self, request, insta_url_encoded, *args, **kwargs):
        uri = (settings.FACEBOOK_GRAPH_URI +
            f'instagram_oembed?url={force_text(urlsafe_base64_decode(insta_url_encoded))}' +
            f'&access_token={settings.FACEBOOK_KEY}|{settings.FACEBOOK_CLIENT_TOKEN}')
        data = json.loads(requests.get(uri).text)
        return JsonResponse(data)
