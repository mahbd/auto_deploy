import json
import os
import subprocess

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from logger.models import Log
from .models import Website, Deploy
from .service_nginx_content import django_service_content, django_nginx_content


def write_superuser(text, path):
    command = ['sudo', 'tee', path]
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        proc.stdin.write(text.encode('utf-8'))
        proc.stdin.close()
        proc.wait()

        if proc.returncode != 0:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='write_superuser',
                               message=f'Could not write to {path} with error: {proc.stderr.read().decode("utf-8")}')
    return True


def execute_command(command: str) -> bool:
    result = os.popen(command).read()
    if result != '':
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='execute_command',
                           message=f'Command "{command}" failed with result: {result}')
    return True


def index(request):
    return render(request, 'deploy/index.html')


def deploy_django(website: Website) -> bool:
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                       message=f'Deploying {website.name} as Django project')
    service_path = os.path.join('/etc', 'systemd', 'system', f'{website.name}.service')
    nginx_path = os.path.join('/etc', 'nginx', 'sites-available', f'{website.name}')
    home_path = os.path.expanduser('~')
    project_path = os.path.join(home_path, 'projects', website.name)
    requirements_path = os.path.join(project_path, 'requirements.txt')
    python_path = os.path.join(project_path, 'venv', 'bin', 'python')
    pip_path = os.path.join(project_path, 'venv', 'bin', 'pip')
    manage_path = os.path.join(project_path, 'manage.py')

    if not os.path.exists(python_path):
        if execute_command(f'cd {project_path} && python3 -m venv venv'):
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                               message=f'Virtual environment created for {website.name}')
        else:
            return False

    if execute_command(f'cd {project_path} && {pip_path} install -r {requirements_path}'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Requirements installed for {website.name}')
    else:
        return False

    if execute_command(f'cd {project_path} && {python_path} {manage_path} migrate'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Migrations applied for {website.name}')
    else:
        return False
    if execute_command(f'cd {project_path} && {python_path} {manage_path} collectstatic --noinput'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Static files collected for {website.name}')
    else:
        return False

    if os.path.exists(service_path):
        if execute_command(f'sudo systemctl restart {website.name}'):
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                               message=f'Service {website.name} restarted')
            return True

    service_content = django_service_content(website)
    if not write_superuser(service_content, service_path):
        return False
    if not execute_command(f'sudo systemctl daemon-reload'):
        return False
    if not execute_command(f'sudo systemctl start {website.name}'):
        return False
    if not execute_command(f'sudo systemctl enable {website.name}'):
        return False
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                       message=f'Service {website.name} started')

    if os.path.exists(nginx_path):
        if execute_command('sudo systemctl restart nginx'):
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                               message=f'Nginx restarted')
            return True
        return False
    nginx_content = django_nginx_content(website)
    if not write_superuser(nginx_content, nginx_path):
        return False
    if not execute_command(f'sudo ln -s {nginx_path} /etc/nginx/sites-enabled'):
        return False
    if not execute_command(f'sudo systemctl restart nginx'):
        return False
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                       message=f'Nginx restarted')
    return True


def get_website(request: WSGIRequest) -> Website | None:
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='get_website',
                       message=f'Processing request')
    payload = request.POST
    if not payload:
        return None
    payload = json.loads(payload['payload'])
    ssh_url: str = payload['repository']['ssh_url']
    if Website.objects.filter(ssh_url=ssh_url).exists():
        return Website.objects.get(ssh_url=ssh_url)
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='get_website',
                       message=f'Website not found for {ssh_url}')
    return None


def pull_website(website: Website) -> bool:
    if not website.deploy_key:
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='pull_website',
                           message=f'Deploy key not found for {website.name}')
        return False
    project_root = os.path.join(os.path.expanduser("~"), "projects")
    project_path = os.path.join(project_root, website.name)
    full_repo_name = website.ssh_url.split(':')[1]
    if os.path.exists(project_path):
        pull_command = f'cd {project_path} && git pull git@github.com-{website.name}:{full_repo_name}'
        return execute_command(pull_command)
    clone_command = f'cd {project_root} && git clone git@github.com-{website.name}:{full_repo_name}'
    if execute_command(clone_command):
        repo_name = full_repo_name.split('/')[-1][:-4]
        if repo_name != website.name:
            return execute_command(f'cd {project_root} && mv {repo_name} {website.name}')
    return False


@require_POST
def deploy(request):
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy',
                       message=f'{request.method} request received')
    website = get_website(request)
    if not website:
        return HttpResponse('Website not found')
    if not pull_website(website):
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='deploy',
                           message=f'Pull failed for {website.name}')
        return HttpResponse('Pull failed')
    if website.framework == Website.CHOICE_DJANGO:
        if deploy_django(website):
            Deploy.objects.create(website=website, is_success=True)
        else:
            Deploy.objects.create(website=website, is_success=False)
    return HttpResponse('Deployed')
