from django.contrib import admin

from .models import Website, DeployKey, Deploy, Environment, Command


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'framework', 'domain', 'is_active', 'certificate')
    list_filter = ('framework', 'is_active', 'certificate')
    search_fields = ('name', 'git_url', 'domain', 'certificate', 'cert_mail')


admin.site.register(DeployKey)
admin.site.register(Deploy)
admin.site.register(Environment)
admin.site.register(Command)
