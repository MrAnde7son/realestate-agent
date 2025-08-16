from django.db import models
class Alert(models.Model):
    user_id = models.CharField(max_length=128)
    criteria = models.JSONField()
    notify = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Alert({self.user_id}, active={self.active})"
