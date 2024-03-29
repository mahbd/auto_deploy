import os

from deploy.models import Website


def django_service_content(website: Website):
    env_text = ""
    for env in website.environment_set.all():
        env_text += f'\nEnvironment="{env.key}={env.value}"'

    home_path = os.path.expanduser('~')
    project_path = os.path.join(home_path, 'projects', website.name)
    socket_path = os.path.join(home_path, 'run', f'{website.name}.sock')
    daphne_path = os.path.join(project_path, 'venv', 'bin', 'daphne')
    return f'''[Unit]
Description={website.name} daphne service
After=network.target
Requires={website.name}.service

[Service]
Type=simple
User={home_path.split('/')[-1]}{env_text}
WorkingDirectory={os.path.join(home_path, 'projects', website.name)}
ExecStart={daphne_path} -u {socket_path} {website.name}.asgi:application

[Install]
WantedBy=multi-user.target
'''


def django_nginx_content(website: Website):
    home_path = os.path.expanduser('~')
    project_path = os.path.join(home_path, 'projects', website.name)
    socket_path = os.path.join(home_path, 'run', f'{website.name}.sock')

    return f'''server {{
    listen 80;
    server_name {website.domain};
    location = /favicon.ico {{ access_log off; log_not_found off; }}
    location /static/ {{
        root {project_path};
    }}
    location /media/ {{
        root {project_path};
    }}
    location / {{
        include proxy_params;
        proxy_pass http://unix:{socket_path};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
        proxy_headers_hash_max_size 1024;
        proxy_headers_hash_bucket_size 128;
    }}
}}
'''


def react_nginx_content(website: Website):
    return f'''server {{
    listen 80;
    server_name {website.domain};
    root {os.path.join(os.path.expanduser('~'), 'projects', website.name, 'build')};
    location = /favicon.ico {{ access_log off; log_not_found off; }}
    location / {{
        try_files $uri /index.html;
    }}
}}
'''


def static_nginx_content(website: Website):
    project_path = os.path.join(os.path.expanduser('~'), 'projects', website.name)
    return f'''server {{
    listen 80;
    server_name {website.domain};
    location = /favicon.ico {{ access_log off; log_not_found off; }}
    index index.html index.htm index.php;
    location / {{
        root {project_path};
    }}
}}
'''
