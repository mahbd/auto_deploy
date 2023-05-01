import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from logger.models import Log
from .models import Website, DeployKey


def execute_command(command: str) -> bool:
    result = os.popen(command).read()
    if result != '':
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='execute_command',
                           message=f'Command "{command}" failed with result: {result}')
    return True


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

        # create config file for GitHub
        config_path = os.path.join(home_path, '.ssh', 'config')
        config_content = ""
        for deploy_key in DeployKey.objects.all():
            config_content += f'Host github.com-{deploy_key.website.name}\n'
            config_content += f'    Hostname github.com\n'
            config_content += f'    IdentityFile={deploy_key.private_path}\n'

        with open(config_path, 'w+') as f:
            f.write(config_content)
