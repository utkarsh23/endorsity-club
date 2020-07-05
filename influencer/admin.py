from django.contrib import admin

from influencer.models import InfluencerStatistics, EndorsingPost

class InfluencerStatisticsAdmin(admin.ModelAdmin):
    list_display = ('influencer',)
    list_filter = ('influencer', )
    fieldsets = (
        (None, {'fields': ('influencer', 'audience_city', 'audience_gender_age', 'impressions', 'follower_counts')}),
    )


class EndorsingPostAdmin(admin.ModelAdmin):
    list_display = ('influencer', 'campaign', 'media_embed_url')
    list_filter = ('influencer', 'campaign')


admin.site.register(InfluencerStatistics, InfluencerStatisticsAdmin)
admin.site.register(EndorsingPost, EndorsingPostAdmin)
