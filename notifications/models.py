from django.db import models

from accounts.models import User

class Notification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    link = models.TextField()
    is_seen = models.BooleanField(default=False)
