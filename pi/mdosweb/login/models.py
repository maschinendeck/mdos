from django.db import models
from django.contrib.auth.models import User

class LogEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="auth_user")
    action = models.CharField(max_length=100)
    ip = models.GenericIPAddressField()

    def __unicode__(self):
        return u"{0.timestamp} - {0.user} ({0.ip}) - {0.action}".format(self)

