import json
import os

from django.http import HttpResponse
from django.shortcuts import render

from .models import Website
from .service_nginx_content import django_service_content, django_nginx_content


def index(request):
    return render(request, 'deploy/index.html')


def deploy_django(website: Website):
    service_path = os.path.join('etc', 'systemd', 'system', f'{website.name}.service')
    nginx_path = os.path.join('etc', 'nginx', 'sites-available', f'{website.name}')
    home_path = os.path.expanduser('~')
    project_path = os.path.join(home_path, 'projects', website.name)
    requirements_path = os.path.join(project_path, 'requirements.txt')
    python_path = os.path.join(project_path, 'venv', 'bin', 'python')
    pip_path = os.path.join(project_path, 'venv', 'bin', 'pip')
    manage_path = os.path.join(project_path, 'manage.py')

    if not os.path.exists(python_path):
        os.system(f'cd {project_path} && python3 -m venv venv')

    if os.path.exists(requirements_path):
        os.system(f'cd {project_path} && {pip_path} install -r requirements.txt')

    if os.path.exists(manage_path):
        os.system(f'cd {project_path} && {python_path} manage.py collectstatic --noinput')

    if os.path.exists(service_path):
        os.system(f'sudo systemctl daemon-reload')
        os.system(f'sudo systemctl restart {website.name}')
    else:
        service_content = django_service_content(website)
        with open(service_path, 'w+') as f:
            f.write(service_content)
        os.system(f'sudo systemctl daemon-reload')
        os.system(f'sudo systemctl enable {website.name}')
        os.system(f'sudo systemctl start {website.name}')

        if os.path.exists(nginx_path):
            os.system(f'sudo systemctl restart nginx')
        else:
            nginx_content = django_nginx_content(website)
            with open(nginx_path, 'w+') as f:
                f.write(nginx_content)
            os.system(f'sudo ln -s {nginx_path} /etc/nginx/sites-enabled')
            os.system(f'sudo systemctl restart nginx')


def deploy(request):
    payload = request.POST
    if payload:
        data = json.loads(payload['payload'])
        html_url = data['repository']['html_url']
        git_url: str = data['repository']['git_url']
        if Website.objects.filter(git_url=git_url).exists():
            website = Website.objects.get(git_url=git_url)
        elif Website.objects.filter(git_url=html_url).exists():
            website = Website.objects.get(git_url=html_url)
        else:
            print('Website not found: ', git_url)  # ToDo: Log this
            return HttpResponse('Website not found')
        if website.deploy_key:
            project_root = os.path.join(os.path.expanduser("~"), "projects")
            project_path = os.path.join(project_root, website.name)
            if not os.path.exists(project_path):
                os.system(f'cd {project_root} && git clone git@github.com-{website.name}:{git_url.split("github.com/")[1]}')
            else:
                os.system(f'cd {project_path} && git pull git@github.com-{website.name}:{git_url.split("github.com/")[1]}')

            if website.framework == Website.CHOICE_DJANGO:
                deploy_django(website)
        else:
            print('Deploy key not found')  # ToDo: Log this
            return HttpResponse('Deploy key not found')
    else:
        print('No payload')
        return HttpResponse('No payload')
    return HttpResponse('Deployed')
