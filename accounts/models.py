import os
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.dispatch import receiver
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django_celery_beat.models import PeriodicTask

from accounts.managers import UserManager


def get_profile_picture_path(instance, filename):
    new_filename = urlsafe_base64_encode(force_bytes(instance.pk)) + '.JPEG'
    old_file_path = os.path.join(
        settings.BASE_DIR,
        'media/profile/',
        new_filename,
    )
    if os.path.isfile(old_file_path):
        os.remove(old_file_path)
    return os.path.join('profile/', new_filename)


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_brand = models.BooleanField(default=False)
    is_account_activated = models.BooleanField(default=True)
    is_google_account = models.BooleanField(default=True)
    is_registered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to=get_profile_picture_path, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def is_it_brand(self):
        return self.is_brand

    @property
    def is_it_account_activated(self):
        return self.is_account_activated

    @property
    def is_it_registered(self):
        return self.is_registered

    @property
    def is_it_google_account(self):
        return self.is_google_account

    @property
    def get_profile_picture(self):
        return self.profile_picture


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=10)
    website = models.URLField(max_length=200, blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True, null=True)
    is_subscription_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    latitude = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    city = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Influencer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)
    is_unlocked = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email


class FacebookPermissions(models.Model):
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE)
    pages_read_engagement = models.BooleanField(default=False)
    instagram_basic = models.BooleanField(default=False)
    instagram_manage_insights = models.BooleanField(default=False)
    pages_show_list = models.BooleanField(default=False)
    user_token = models.TextField()
    user_id = models.TextField()
    fb_page_id = models.TextField()
    ig_page_id = models.TextField()
    ig_username = models.CharField(max_length=200, blank=True)
    ig_follower_count = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Facebook Permissions'
    
    def __str__(self):
        return self.influencer.user.email

    @property
    def has_all_permissions(self):
        return (self.pages_read_engagement and
            self.instagram_basic and
            self.pages_show_list and
            self.instagram_manage_insights)


@receiver(models.signals.post_delete, sender=User)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `User` object is deleted.
    """
    if instance.profile_picture:
        if os.path.isfile(instance.profile_picture.path):
            os.remove(instance.profile_picture.path)


@receiver(models.signals.post_delete, sender=Influencer)
def auto_delete_celery_task_on_delete(sender, instance, **kwargs):
    user_pk = instance.user.pk
    celery_user_token_periodic_task = PeriodicTask.objects.filter(
        name=f'Influencer {user_pk} Update User Token'
    )
    if celery_user_token_periodic_task.exists():
        celery_user_token_periodic_task.delete()

    celery_follower_count_periodic_task = PeriodicTask.objects.filter(
        name=f'Influencer {user_pk} Update Follower Count'
    )
    if celery_follower_count_periodic_task.exists():
        celery_follower_count_periodic_task.delete()
