from django import forms

from accounts.models import Location

class AddLocationForm(forms.Form):
    store_location = forms.CharField(max_length=500)
