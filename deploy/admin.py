import datetime

from django.contrib import admin

from .models import Website, DeployKey, Deploy, Environment, Command
from .shortcuts import execute_command
from .views import pull_website, deploy_now


class EnvironmentInline(admin.TabularInline):
    model = Environment
    extra = 0


class CommandInline(admin.TabularInline):
    model = Command
    extra = 0


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    actions = ('action_generate_certificate', 'action_deploy_now')
    inlines = (EnvironmentInline, CommandInline)
    list_display = ('name', 'framework', 'domain', 'is_active', 'certificate')
    list_filter = ('framework', 'is_active', 'certificate')
    readonly_fields = ('deploy_key',)
    search_fields = ('name', 'git_url', 'domain', 'certificate', 'cert_mail')

    def action_generate_certificate(self, request, queryset):
        for website in queryset:
            command = f"sudo certbot --non-interactive --redirect --agree-tos --nginx -d {website.domain} -m {website.cert_mail}"
            execute_command(command)
            website.certificate = datetime.date.today()
            website.save()
        updated = queryset.count()
        self.message_user(request, f'{updated} website{" was" if updated == 1 else "s were"} certificate updated')
    action_generate_certificate.short_description = 'Gen/Update Certificate'

    def action_deploy_now(self, request, queryset):
        for website in queryset:
            pull_website(website)
            deploy_now(website)
        updated = queryset.count()
        self.message_user(request, f'{updated} website{" was" if updated == 1 else "s were"} deployed')
    action_deploy_now.short_description = 'Deploy Now'


@admin.register(DeployKey)
class DeployKeyAdmin(admin.ModelAdmin):
    list_display = ('id', 'website', 'public_key')
    search_fields = ('website__name',)

    @admin.display(description='Website', ordering='website__name')
    def website(self, deploy_key: DeployKey):
        return deploy_key.website.name


@admin.register(Deploy)
class DeployAdmin(admin.ModelAdmin):
    list_display = ('id', 'website', 'is_success', 'deploy_time')
    list_filter = ('website', 'is_success', 'deploy_time')
    search_fields = ('website__name',)


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'website', 'key', 'value')
    list_filter = ('website',)
    search_fields = ('key', 'value')
    list_editable = ('key', 'value')
    autocomplete_fields = ('website',)


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('id', 'website', 'command')
    list_filter = ('website',)
    search_fields = ('command', 'website__name')
    list_editable = ('command',)
    autocomplete_fields = ('website',)
