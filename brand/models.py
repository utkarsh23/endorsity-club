import uuid

from django.db import models

from accounts.models import Brand


class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField() # typically 30 days from start_time
