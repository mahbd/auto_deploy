import json
import os

from django.http import HttpResponse
from django.shortcuts import render

from logger.models import Log
from .models import Website
from .service_nginx_content import django_service_content, django_nginx_content


def index(request):
    return render(request, 'deploy/index.html')


def deploy_django(website: Website):
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
        error = os.system(f'cd {project_path} && python3 -m venv venv')
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Venv created')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Venv creation failed. Error code: {error}')

    if os.path.exists(requirements_path):
        error = os.system(f'cd {project_path} && {pip_path} install -r requirements.txt')
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Requirements installed')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Requirements installation failed. Error code: {error}')

    if os.path.exists(manage_path):
        error = os.system(f'cd {project_path} && {python_path} manage.py migrate')
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Migrations applied')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Migrations failed. Error code: {error}')
        error = os.system(f'cd {project_path} && {python_path} manage.py collectstatic --noinput')
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Static files collected')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Static files collection failed. Error code: {error}')

    if os.path.exists(service_path):
        command = f'echo ""|sudo -S systemctl daemon-reload'
        error = os.system(command)
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'daemon reloaded')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'daemon reload failed. Error code: {error}')
        command = f'echo ""|sudo -S systemctl restart {website.name}'
        error = os.system(command)
        if error == 0:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Service {website.name} restarted')
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Service {website.name} restart failed. Error code: {error}. command={command}')
    else:
        service_content = django_service_content(website)
        with open(service_path, 'w+') as f:
            f.write(service_content)
        os.system(f'echo ""|sudo -S systemctl daemon-reload')
        os.system(f'echo ""|sudo -S systemctl start {website.name}')
        os.system(f'echo ""|sudo -S systemctl enable {website.name}')
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                           message=f'Service {website.name} started')

        if os.path.exists(nginx_path):
            os.system(f'echo ""|sudo -S systemctl restart nginx')
        else:
            nginx_content = django_nginx_content(website)
            with open(nginx_path, 'w+') as f:
                f.write(nginx_content)
            os.system(f'echo ""|sudo -S ln -s {nginx_path} /etc/nginx/sites-enabled')
            os.system(f'echo ""|sudo -S systemctl restart nginx')
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy_django',
                               message=f'Nginx restarted')


def deploy(request):
    Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                       message=f'{request.method} request received')
    payload = request.POST
    if payload:
        data = json.loads(payload['payload'])
        html_url = data['repository']['html_url']
        ssh_url: str = data['repository']['ssh_url']
        if Website.objects.filter(git_url=ssh_url).exists():
            website = Website.objects.get(git_url=ssh_url)
        elif Website.objects.filter(git_url=html_url).exists():
            website = Website.objects.get(git_url=html_url)
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                               message=f'Website not found for {ssh_url}')
            return HttpResponse('Website not found')
        if website.deploy_key:
            project_root = os.path.join(os.path.expanduser("~"), "projects")
            project_path = os.path.join(project_root, website.name)
            if not os.path.exists(project_path):
                command = f'cd {project_root} && git clone git@github.com-{website.name}:{ssh_url.split("github.com/")[1]}'
                Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                                   message=f'Cloning using {command}')
                os.system(command)
                if data['repository']['name'] != website.name:
                    os.system(f'cd {project_root} && mv {data["repository"]["name"]} {website.name}')
            else:
                command = f'cd {project_path} && git pull git@github.com-{website.name}:{ssh_url.split("github.com/")[1]}'
                Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                                   message=f'Pulling using {command}')
                os.system(command)

            if website.framework == Website.CHOICE_DJANGO:
                deploy_django(website)
        else:
            Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                               message=f'Deploy key not found for {website.name}')
            return HttpResponse('Deploy key not found')
    else:
        Log.objects.create(log_type=Log.LOG_TYPE_INFO, location='auto_deploy.deploy.views.deploy',
                           message=f'No payload')
        print('No payload')
        return HttpResponse('No payload')
    return HttpResponse('Deployed')
