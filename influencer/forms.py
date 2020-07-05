from django import forms

from accounts.models import Brand, Location


class LocationSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        brand = Brand.objects.get(id=kwargs.pop('brand_uuid'))
        locations = Location.objects.filter(brand=brand)
        location_choices = []
        for location in locations:
            location_choices.append((location.id, location.name))
        super().__init__(*args, **kwargs)
        self.fields['location'] = forms.ChoiceField(choices=location_choices)
