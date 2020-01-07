import os
import random
from fabric import Connection
from fabric.tasks import task
from patchwork.files import append, exists


REPO_URL = 'https://github.com/hettlage/superlists.git'


@task
def deploy(c):
    site_folder = f"/home/{os.environ['REMOTE_USER']}/sites/{os.environ['SERVER']}"
    c.run(f"mkdir -p {site_folder}")
    current_commit = c.local('git log -n 1 --format=%H').stdout.strip()
    with c.cd(site_folder):
        _get_latest_source(c, site_folder, current_commit)
        _update_virtual_env(c)
        _create_or_update_dotenv()
        _update_static_files()
        _update_database(c)


def _exists(c, folder):
    return not c.run(f'test -d {folder}', warn=True).failed


def _get_latest_source(c, site_folder, current_commit):
    if not exists(c, site_folder):
        c.run("git pull")
    else:
        c.run(f"git clone {REPO_URL} .")

    c.run(f'git reset --hard {current_commit}')


def _update_virtual_env(c):
    if not exists(c, 'venv/bin/pip'):
        c.run('python3 -m venv venv')
    c.run('pip install -r requirements.txt')


def _create_or_update_dotenv(c):
    append('.env', 'PRODUCTION_MODE','y')
    append('.env', f"SITENAME={os.environ['HOST']}")
    current_contents = c.run("cat .env")
    if 'DJANGO_SECRET_KEY' not in current_contents:
        new_secret = ''.join(random.SystemRandom().choices('abcdefghijklmnopqrstuvwxyz0123456789', k=50))
        append('.env', f"DJANGO_SECRET_KEY={new_secret}")


def _update_static_files(c):
    c.run('./venv/bin/python manage.py collectstatic --noinput')


def _update_database(c):
    c.run('./venv/bin/python manage.py migrate --noinput')
