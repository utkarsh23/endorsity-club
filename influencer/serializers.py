from django.core.serializers.json import Serializer


class BrandsViewSerializer(Serializer):

    def get_dump_object(self, obj):
        data = super().get_dump_object(obj)
        data['fields']['profile_picture'] = (
            obj.user.get_profile_picture.url
            if obj.user.get_profile_picture
            else None)
        return data


brands_view_serializer = BrandsViewSerializer()
