from django.contrib import admin

from .models import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('log_type', 'location', 'message', 'created_at')
    list_filter = ('log_type', 'created_at')
    search_fields = ('location', 'text')
