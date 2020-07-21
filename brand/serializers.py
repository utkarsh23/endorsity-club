from django.core.serializers.json import Serializer
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import FacebookPermissions


class InfluencersViewSerializer(Serializer):

    def get_dump_object(self, obj):
        data = super().get_dump_object(obj)
        data['fields']['user_encoded_pk'] = urlsafe_base64_encode(force_bytes(obj.user.pk))
        data['fields']['profile_picture'] = (
            obj.user.get_profile_picture.url
            if obj.user.get_profile_picture
            else None)
        fb_permissions = FacebookPermissions.objects.get(influencer=obj)
        data['fields']['username'] = fb_permissions.ig_username
        data['fields']['follower_count'] = fb_permissions.ig_follower_count
        return data


influencers_view_serializer = InfluencersViewSerializer()
