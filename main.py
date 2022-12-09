import os
import threading

from fastapi import FastAPI

app = FastAPI()

git_rep_data = {
    "mahbd/auto_deploy": {
        "app_type": "fastapi",
        "dir": "/home/mah/projects/auto_deploy",
        "pip_install": "/home/mah/projects/auto_deploy/venv/bin/pip3 install -r requirements.txt",
        "extra_commands": [],
        "restart": "sudo systemctl restart auto_deploy",
    },
    "mahbd/todo-api": {
        "app_type": "django",
        "dir": "/home/mah/projects/todo-api",
        "pip_install": "/home/mah/projects/todo-api/venv/bin/pip3 install -r requirements.txt",
        "extra_commands": [
            "/home/mah/projects/todo-api/venv/bin/python3 manage.py migrate",
            "/home/mah/projects/todo-api/venv/bin/python3 manage.py collectstatic --noinput",
        ],
        "restart": "sudo systemctl restart todo-api",
    }
}


@app.get("/")
def read_root():
    return {"message": "Hello World"}


def deploy_repo(repo_data):
    os.chdir(repo_data["dir"])
    os.system("git pull")
    if repo_data["app_type"] == "fastapi":
        os.system(repo_data["pip_install"])
        for command in repo_data["extra_commands"]:
            os.system(command)
        os.system(repo_data["restart"])
    elif repo_data["app_type"] == "django":
        os.system(repo_data["pip_install"])
        for command in repo_data["extra_commands"]:
            os.system(command)
        os.system(repo_data["restart"])


@app.post("/github/")
def github_webhook(payload: dict):
    repo_name = payload["repository"]["full_name"]
    if repo_name in git_rep_data:
        repo_data = git_rep_data[repo_name]
        print("Deploying " + repo_name)
        with open("log.txt", "a+") as f:
            f.write("Deploying " + repo_name)
        threading.Thread(target=deploy_repo, args=(repo_data,)).start()
    else:
        print(f"Repo {repo_name} not found")
        with open("log.txt", "a+") as f:
            f.write(f"Repo {repo_name} not found")
    return {"response": True}
