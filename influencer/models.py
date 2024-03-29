import uuid

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.dispatch import receiver

from accounts.models import (
    Influencer,
    FacebookPermissions,
    Location,
)

from brand.models import Campaign

from django_celery_beat.models import PeriodicTask


class InfluencerStatistics(models.Model):
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE)
    audience_city = ArrayField(
        ArrayField(
            models.TextField(),
            size=2
        ),
        null=True,
    )
    audience_gender_age = ArrayField(
        ArrayField(
            models.TextField(),
            size=2
        ),
        null=True,
    )
    impressions = ArrayField(
        ArrayField(
            models.TextField(),
            size=2
        ),
        null=True,
    )
    follower_counts = ArrayField(
        ArrayField(
            models.TextField(),
            size=2
        ),
        null=True,
    )

    class Meta:
        verbose_name_plural = 'Influencer Statistics'

    def __str__(self):
        return FacebookPermissions.objects.get(influencer=self.influencer).ig_username


class EndorsingPost(models.Model):
    MEDIA_CHOICES = (
        ('IMAGE', 'IMAGE'),
        ('VIDEO', 'VIDEO'),
        ('CAROUSEL_ALBUM', 'CAROUSEL_ALBUM'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    media_id = models.TextField()
    media_embed_url = models.URLField(max_length=1000)
    media_type = models.CharField(max_length=20, choices=MEDIA_CHOICES)
    complete = models.BooleanField(default=False)
    engagement = models.TextField()
    impressions = models.TextField()
    reach = models.TextField()
    saved = models.TextField()
    video_views = models.TextField()

    def __str__(self):
        return FacebookPermissions.objects.get(influencer=self.influencer).ig_username


@receiver(models.signals.post_delete, sender=Influencer)
def auto_delete_influencer_statistics_on_delete(sender, instance, **kwargs):
    user_pk = instance.user.pk
    celery_influencer_statistics_periodic_task = PeriodicTask.objects.filter(
        name=f'Influencer {user_pk} Update Influencer Statistics'
    )
    if celery_influencer_statistics_periodic_task.exists():
        celery_influencer_statistics_periodic_task.delete()


@receiver(models.signals.post_delete, sender=EndorsingPost)
def auto_delete_influencer_post_celery_task(sender, instance, **kwargs):
    celery_influencer_post_periodic_task = PeriodicTask.objects.filter(
        name=f'Influencer {instance.influencer.user.pk} Update Post {instance.id} Statistics'
    )
    if celery_influencer_post_periodic_task.exists():
        celery_influencer_post_periodic_task.delete()
