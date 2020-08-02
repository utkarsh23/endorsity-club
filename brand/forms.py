from django import forms

from accounts.models import Location, Brand

class AddLocationForm(forms.Form):
    store_location = forms.CharField(max_length=500)


class ActiveLocationsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        brand = Brand.objects.get(id=kwargs.pop('brand_uuid'))
        locations = Location.objects.filter(brand=brand).order_by('id')
        location_choices = []
        for location in locations:
            location_choices.append((location.id, location.name))
        super().__init__(*args, **kwargs)
        self.fields['location'] = forms.MultipleChoiceField(
            choices=location_choices,
            widget=forms.CheckboxSelectMultiple,
        )
        self.initial['location'] = [location.id for location in locations if location.active]
