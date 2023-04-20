from django.db import models


class Environment(models.Model):
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)


class Command(models.Model):
    command = models.CharField(max_length=255)


class DeployKey(models.Model):
    public_key = models.CharField(max_length=1023)
    public_path = models.CharField(max_length=255)
    private_path = models.CharField(max_length=255)


class Website(models.Model):
    CHOICE_DJANGO = 'django'
    CHOICE_FLASK = 'flask'
    CHOICE_FASTAPI = 'fastapi'
    CHOICE_EXPRESS = 'express'
    CHOICE_REACT = 'react'
    CHOICE_SVELTE = 'svelte'
    CHOICE_DJANGO_REACT = 'django-react'
    CHOICE_DJANGO_SVELTE = 'django-svelte'
    FRAMEWORK_CHOICES = [
        (CHOICE_DJANGO, 'Django'),
        (CHOICE_FLASK, 'Flask'),
        (CHOICE_FASTAPI, 'FastAPI'),
        (CHOICE_EXPRESS, 'Express'),
        (CHOICE_REACT, 'React'),
        (CHOICE_SVELTE, 'Svelte'),
        (CHOICE_DJANGO_REACT, 'Django-React'),
        (CHOICE_DJANGO_SVELTE, 'Django-Svelte'),
    ]
    name = models.CharField(max_length=255, unique=True)
    framework = models.CharField(max_length=50, choices=FRAMEWORK_CHOICES)
    git_url = models.URLField()
    environments = models.ManyToManyField(Environment, blank=True)
    extra_commands = models.ManyToManyField(Command, blank=True)
    is_active = models.BooleanField(default=True)
    certificate = models.DateField(null=True, blank=True)
    cert_mail = models.EmailField(default='mahmudula2000@gmail.com')
    domain = models.URLField(null=True, blank=True)
    deploy_key = models.ForeignKey(DeployKey, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ('name',)


class Deploy(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    is_success = models.BooleanField()
    deploy_time = models.DateTimeField(auto_now_add=True)
    logs = models.TextField()

    class Meta:
        ordering = ('-deploy_time',)
