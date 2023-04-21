# Generated by Django 4.2 on 2023-04-21 03:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='website',
            name='environments',
        ),
        migrations.AddField(
            model_name='environment',
            name='website',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='deploy.website'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='website',
            name='framework',
            field=models.CharField(choices=[('django', 'Django'), ('flask', 'Flask'), ('fastapi', 'FastAPI'), ('express', 'Express'), ('react', 'React'), ('svelte', 'Svelte'), ('django-react', 'Django-React'), ('django-svelte', 'Django-Svelte')], max_length=50),
        ),
    ]