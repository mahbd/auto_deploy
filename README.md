# Auto Deploy

Auto Deploy is a Django-based web application that listens for GitHub webhook events and automates the process of deploying your projects (Django, React, Static, etc.) to your server environment. It manages SSH deploy keys, environment variables, systemd services, and Nginx configurations, making continuous deployment seamless and hands-off.

## Features

- **Automated Deploy Key Management**

  - Generates a new SSH key pair for each registered website.
  - Updates `~/.ssh/config` to use the correct identity file per host.

- **Framework Support**

  - Django (with migrations, static collection, systemd, and Nginx)
  - React (npm install, build, Nginx)
  - Static sites (simple Nginx serve)

- **Systemd Service Generation (Django only)**

  - Creates/updates a systemd unit file for Django ASGI via Daphne.
  - Reloads, restarts, and enables services automatically.

- **Nginx Configuration**

  - Generates site configs under `/etc/nginx/sites-available` and symlinks to `sites-enabled`.
  - Hot-reloads Nginx on changes to domain or new deploys.

- **Environment Variable Management**

  - Stores key/value pairs per website.
  - Injects as systemd `Environment=` entries and during migration/collectstatic commands.

- **Repository Pull & Clone**

  - Clones a new repo into `~/projects/<website.name>` on first deploy.
  - Pulls latest changes on subsequent deploys.

- **Logging**

  - Records detailed logs of commands, errors, and steps in a `logger` app.
  - Stores logs in database with timestamps and types (info, command, error).

- **Webhooks Endpoint**

  - Exposes a `/deploy/` endpoint (csrf-exempt) to receive GitHub push events.
  - Validates repository SSH URL against registered websites.

- **Cleanup Hooks**
  - Deletes systemd, Nginx configs, project folders, and SSH keys when a Website record is removed.

## Requirements

- Python 3.11+
- Django 4.2+
- Git
- Node.js & npm (for React projects)
- Nginx
- systemd (Linux)

## Installation & Setup

1. **Clone this repository:**

   ```powershell
   git clone <your-repo-url>
   cd auto_deploy
   ```

2. **Create a Python virtual environment and install dependencies:**

   ```powershell
   python3.11 -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Run migrations:**

   ```powershell
   python manage.py migrate
   ```

4. **Create a superuser (optional):**

   ```powershell
   python manage.py createsuperuser
   ```

5. **Start the Django development server:**

   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

6. **Access the admin panel:**  
   Visit `http://localhost:8000/admin/` to register `Website` entries and configure environment variables.

## Configuration

1. **Register a Website:**  
   In the Django admin, add a new Website with fields:

   - **Name:** Unique identifier, used for folder/service names.
   - **Framework:** Select one of the supported frameworks.
   - **SSH URL:** The GitHub SSH clone URL (e.g., `git@github.com:user/repo.git`).
   - **Domain:** The public domain name for Nginx config.
   - **Certificate Date & Email:** Optional fields for SSL reminders.

2. **Add Environment Variables:**  
   Under the `Environment` model in admin, add any key/value pairs the application needs at runtime.

3. **Set Up Webhook:**  
   In your GitHub repository settings, add a webhook:
   - **Payload URL:** `http://<server-ip>:8000/deploy/`
   - **Content Type:** `application/x-www-form-urlencoded`
   - **Secret:** (optional) use your own secret handling logic.
   - **Events:** `Push events`.

## Usage

Once configured, GitHub push events will trigger the following pipeline:

1. **Webhook Received:**  
   `/deploy/` endpoint parses payload, matches SSH URL to a registered Website.

2. **Clone or Pull Repo:**  
   New site: clones into `~/projects/<name>`;  
   Existing site: runs `git pull`.

3. **Install Dependencies & Build:**

   - Django: sets up/updates venv, installs `requirements.txt`, runs `migrate`, `collectstatic`.
   - React: runs `npm install`, `npm run build`.
   - Static: no build step.

4. **Systemd & Nginx Updates:**

   - Django: regenerates service unit and reloads systemd.
   - All: generates or updates Nginx server block, reloads Nginx.

5. **Logging:**  
   Each step logs success or errors in the `logger` database.

### Manual Deploy Trigger

You can also manually trigger deployment via Django shell:

```powershell
python manage.py shell
> from deploy.models import Website
> from deploy.views import deploy_now
> website = Website.objects.get(name="my-site")
> deploy_now(website)
```

## Project Structure

```
manage.py
requirements.txt
payload.json        # Example webhook payload

auto_deploy/        # Django project settings
  ├─ settings.py
  ├─ urls.py
  └─ wsgi.py

deploy/             # Main deployment app
  ├─ models.py       # Website, Environment, DeployKey, Deploy
  ├─ signals.py      # Auto hooks for systemd, keys, cleanup
  ├─ service_nginx_content.py
  ├─ shortcuts.py    # Shell command helpers
  └─ views.py        # Webhook processing & deploy logic

logger/             # Logging app
  ├─ models.py       # Log entries
  └─ admin.py

templates/deploy/index.html
```

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am "Add new feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
