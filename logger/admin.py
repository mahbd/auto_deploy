from django.contrib import admin

from .models import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('log_type', 'location', 'message', 'created_at')
    list_filter = ('log_type',)
    search_fields = ('location', 'text')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
