from django.contrib import admin

from influencer.models import InfluencerStatistics

class InfluencerStatisticsAdmin(admin.ModelAdmin):
    list_display = ('influencer',)
    list_filter = ('influencer', )
    fieldsets = (
        (None, {'fields': ('influencer', 'audience_city', 'audience_gender_age', 'impressions', 'follower_counts')}),
    )


admin.site.register(InfluencerStatistics, InfluencerStatisticsAdmin)
