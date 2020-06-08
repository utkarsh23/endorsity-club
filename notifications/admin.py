 
from django.contrib import admin

from notifications.models import Notification

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_seen')
    list_filter = ('user', 'is_seen')
    readonly_fields = ('created_at',)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'created_at',
                    'user',
                    'message',
                    'link',
                    'is_seen'
                )
            }
        ),
    )

admin.site.register(Notification, NotificationAdmin)
