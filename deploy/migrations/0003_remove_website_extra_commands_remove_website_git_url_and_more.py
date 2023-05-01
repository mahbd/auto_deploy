# Generated by Django 4.2 on 2023-05-01 04:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0002_remove_website_environments_environment_website_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='website',
            name='extra_commands',
        ),
        migrations.RemoveField(
            model_name='website',
            name='git_url',
        ),
        migrations.AddField(
            model_name='command',
            name='website',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='deploy.website'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='website',
            name='ssh_url',
            field=models.CharField(default='please set', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='website',
            name='deploy_key',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='deploy.deploykey'),
        ),
        migrations.AlterField(
            model_name='website',
            name='domain',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]