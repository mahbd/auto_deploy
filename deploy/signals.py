import os

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Website, DeployKey, Environment
from .service_nginx_content import django_service_content
from .shortcuts import execute_command, write_superuser


def update_ssh_config_file(home_path):
    config_path = os.path.join(home_path, '.ssh', 'config')
    config_content = ""
    for deploy_key in DeployKey.objects.all():
        config_content += f'Host github.com-{deploy_key.website.name}\n'
        config_content += f'    Hostname github.com\n'
        config_content += f'    IdentityFile={deploy_key.private_path}\n'
    with open(config_path, 'w+') as f:
        f.write(config_content)


@receiver(post_save, sender=Website)
def create_deploy_key_for_new_website(sender, **kwargs):
    if kwargs['created']:
        website: Website = kwargs['instance']
        home_path = os.path.expanduser('~')
        pub_path = os.path.join(home_path, '.ssh', f'{website.name}.pub')
        private_path = os.path.join(home_path, '.ssh', f'{website.name}')
        if os.path.exists(pub_path):
            os.remove(pub_path)
        if os.path.exists(private_path):
            os.remove(private_path)
        gen_command = f'ssh-keygen -t ed25519 -C "{website.name}" -f "{os.path.join(home_path, ".ssh", website.name)}" -N ""'
        if not execute_command(gen_command):
            raise Exception(f'Could not generate key for {website.name}')
        with open(pub_path, 'r') as f:
            public_key = f.read()
        deploy_key = DeployKey(public_key=public_key, public_path=pub_path, private_path=private_path)
        deploy_key.save()
        website.deploy_key = deploy_key
        website.save()

        update_ssh_config_file(home_path)


@receiver(post_delete, sender=Website)
def clear_disk_for_deleted_website(sender, **kwargs):
    website: Website = kwargs['instance']
    service_path = os.path.join('/etc', 'systemd', 'system', f'{website.name}.service')
    nginx_available_path = os.path.join('/etc', 'nginx', 'sites-available', f'{website.name}')
    nginx_enabled_path = os.path.join('/etc', 'nginx', 'sites-enabled', f'{website.name}')
    if os.path.exists(service_path):
        execute_command(f'sudo systemctl stop {website.name}')
        execute_command(f'sudo systemctl disable {website.name}')
        execute_command(f'sudo rm {service_path}')

    if os.path.exists(nginx_available_path):
        execute_command(f'sudo rm {nginx_available_path}')
    if os.path.exists(nginx_enabled_path):
        execute_command(f'sudo rm {nginx_enabled_path}')
        execute_command(f'sudo systemctl restart nginx')
    project_path = os.path.join(os.path.expanduser("~"), "projects", website.name)
    if os.path.exists(project_path):
        execute_command(f'sudo rm -rf {project_path}')


@receiver(post_delete, sender=DeployKey)
def delete_deploy_key(sender, **kwargs):
    deploy_key: DeployKey = kwargs['instance']
    if os.path.exists(deploy_key.public_path):
        os.remove(deploy_key.public_path)
    if os.path.exists(deploy_key.private_path):
        os.remove(deploy_key.private_path)

    home_path = os.path.expanduser('~')
    update_ssh_config_file(home_path)


@receiver(post_save, sender=Environment)
def update_system_service_after_environment_change(sender, **kwargs):
    environment: Environment = kwargs['instance']
    website: Website = environment.website
    if website.framework == Website.CHOICE_DJANGO:
        service_path = os.path.join('/etc', 'systemd', 'system', f'{website.name}.service')
        if os.path.exists(service_path):
            execute_command(f'sudo systemctl stop {website.name}')
            execute_command(f'sudo rm {service_path}')
        service_content = django_service_content(website)
        write_superuser(service_content, service_path)
        execute_command(f'sudo systemctl daemon-reload')
        execute_command(f'sudo systemctl enable {website.name}')
        execute_command(f'sudo systemctl start {website.name}')
