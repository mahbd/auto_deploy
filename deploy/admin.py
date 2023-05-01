from django.contrib import admin

from .models import Website, DeployKey, Deploy, Environment, Command


class EnvironmentInline(admin.TabularInline):
    model = Environment
    extra = 0


class CommandInline(admin.TabularInline):
    model = Command
    extra = 0


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'framework', 'domain', 'is_active', 'certificate')
    list_filter = ('framework', 'is_active', 'certificate')
    search_fields = ('name', 'git_url', 'domain', 'certificate', 'cert_mail')
    readonly_fields = ('deploy_key',)
    inlines = (EnvironmentInline, CommandInline)


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
