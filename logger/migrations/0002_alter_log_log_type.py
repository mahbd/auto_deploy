# Generated by Django 4.2 on 2023-05-01 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='log_type',
            field=models.CharField(choices=[('command', 'Command'), ('info', 'Info'), ('error', 'Error')], default='info', max_length=10),
        ),
    ]
