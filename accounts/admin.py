from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.forms import (
    AdminUserChangeForm,
    UserCreationForm,
)
from accounts.models import (
    Brand,
    Location,
    Influencer,
    FacebookPermissions
)


UserModel = get_user_model()


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = AdminUserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    readonly_fields = ('created_at',)
    list_display = ('email', 'pk', 'is_admin', 'is_brand')
    list_filter = ('is_admin', 'is_brand')
    fieldsets = (
        (None, {'fields': ('created_at', 'profile_picture', 'email', 'password', 'is_active')}),
        ('Permissions', {'fields': ('is_admin', 'is_brand', 'is_account_activated', 'is_registered', 'is_google_account')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class BrandAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_subscription_active')
    list_filter = ('name', 'is_subscription_active')
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Details', {'fields': ('name', 'phone_number', 'website', 'instagram_handle', 'is_subscription_active')}),
    )


class LocationAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'active', 'latitude', 'longitude', 'city')
    list_filter = ('brand', 'active', 'city')
    readonly_fields = ('id',)
    fieldsets = (
        (None, {'fields': ('id','brand', 'name', 'active', 'latitude', 'longitude', 'city')}),
    )


class InfluencerAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'is_verified', 'is_unlocked')
    list_filter = ('first_name', 'last_name', 'is_verified', 'is_unlocked')
    fieldsets = (
        (None, {'fields': ('user', 'is_verified', 'is_unlocked')}),
        ('Personal Details', {'fields': ('first_name', 'last_name', 'phone_number')}),
    )


class FacebookPermissionsAdmin(admin.ModelAdmin):
    list_display = (
        'influencer',
        'pages_read_engagement',
        'instagram_basic',
        'instagram_manage_insights',
        'pages_show_list',
        'ig_username',
        'ig_follower_count',
    )
    list_filter = ('pages_read_engagement', 'instagram_basic', 'instagram_manage_insights', 'pages_show_list')
    fieldsets = (
        (None, {'fields': ('influencer',)}),
        (
            'Facebook Details',
            {
                'fields': (
                    'user_token',
                    'user_id',
                    'fb_page_id',
                    'ig_page_id',
                    'ig_username',
                    'ig_follower_count',
                )
            }
        ),
        (
            'Facebook API Permissions',
            {
                'fields': (
                    'pages_read_engagement',
                    'instagram_basic',
                    'instagram_manage_insights',
                    'pages_show_list',
                )
            }
        ),
    )

admin.site.register(Brand, BrandAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Influencer, InfluencerAdmin)
admin.site.register(FacebookPermissions, FacebookPermissionsAdmin)
admin.site.register(UserModel, UserAdmin)
admin.site.unregister(Group)
