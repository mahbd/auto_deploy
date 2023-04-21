from django.db import models


class Log(models.Model):
    LOG_TYPE_INFO = 'info'
    LOG_TYPE_ERROR = 'error'

    LOG_TYPE = (
        (LOG_TYPE_INFO, 'Info'),
        (LOG_TYPE_ERROR, 'Error'),
    )
    log_type = models.CharField(max_length=10, choices=LOG_TYPE, default=LOG_TYPE_INFO)
    location = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
