import json
import os
import threading

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from logger.models import Log
from .models import Website, Deploy
from .service_nginx_content import django_service_content, django_nginx_content, react_nginx_content, \
    static_nginx_content
from .shortcuts import execute_command, write_superuser


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
        if execute_command(f'cd {project_path} && python3.11 -m venv venv'):
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                               message=f'Virtual environment created for {website.name}')
        else:
            return False

    if execute_command(f'cd {project_path} && {pip_path} install -r {requirements_path}'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Requirements installed for {website.name}')
    else:
        return False

    env_txt = ""
    for env in website.environment_set.all():
        env_txt += f'export {env.key}="{env.value}" && '
    if execute_command(f'{env_txt}cd {project_path} && {python_path} {manage_path} migrate'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Migrations applied for {website.name}')
    else:
        return False
    if execute_command(f'{env_txt}cd {project_path} && {python_path} {manage_path} collectstatic --noinput'):
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                           message=f'Static files collected for {website.name}')
    else:
        return False

    if os.path.exists(service_path):
        if execute_command(f'sudo systemctl restart {website.name}'):
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy_django',
                               message=f'Service {website.name} restarted')
    else:
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
        return True
    return False


def deploy_react(website: Website) -> bool:
    project_path = os.path.join(os.path.expanduser("~"), "projects", website.name)
    nginx_path = os.path.join('/etc', 'nginx', 'sites-available', f'{website.name}')
    execute_command(f'cd {project_path} && npm install')
    execute_command(f'cd {project_path} && npm run build')
    if os.path.exists(nginx_path):
        return execute_command('sudo systemctl restart nginx')
    nginx_content = react_nginx_content(website)
    if not write_superuser(nginx_content, nginx_path):
        return False
    execute_command(f'sudo ln -s {nginx_path} /etc/nginx/sites-enabled')
    execute_command(f'sudo systemctl restart nginx')
    return True


def deploy_static(website: Website):
    nginx_path = os.path.join('/etc', 'nginx', 'sites-available', f'{website.name}')
    if os.path.exists(nginx_path):
        return execute_command('sudo systemctl restart nginx')
    nginx_content = static_nginx_content(website)
    if not write_superuser(nginx_content, nginx_path):
        return False
    execute_command(f'sudo ln -s {nginx_path} /etc/nginx/sites-enabled')
    execute_command(f'sudo systemctl restart nginx')
    return True


def deploy_now(website: Website):
    if website.framework == Website.CHOICE_DJANGO:
        if deploy_django(website):
            Deploy.objects.create(website=website, is_success=True)
        else:
            Deploy.objects.create(website=website, is_success=False)
    elif website.framework == Website.CHOICE_REACT:
        if deploy_react(website):
            Deploy.objects.create(website=website, is_success=True)
        else:
            Deploy.objects.create(website=website, is_success=False)
    elif website.framework == Website.CHOICE_STATIC:
        if deploy_static(website):
            Deploy.objects.create(website=website, is_success=True)
        else:
            Deploy.objects.create(website=website, is_success=False)
    return False


@require_POST
def deploy_request(request):
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='deploy',
                       message=f'{request.method} request received')
    website = get_website(request)
    if not website:
        return HttpResponse('Website not found')
    if not pull_website(website):
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='deploy',
                           message=f'Pull failed for {website.name}')
        return HttpResponse('Pull failed')
    threading.Thread(target=deploy_now, args=(website,)).start()
    return HttpResponse('Deployed')
