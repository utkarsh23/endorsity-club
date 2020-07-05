from django.contrib import admin

from brand.models import Campaign


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'start_time', 'end_time')
    list_filter = ('brand',)


admin.site.register(Campaign, CampaignAdmin)
