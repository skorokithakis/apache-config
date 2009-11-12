from __future__ import with_statement
from fabric.api import env, run, sudo, cd, runs_once, prompt
from fabric.contrib.files import exists, upload_template

import posixpath

ROOT_PATH = "/home/projects/"

env.paths = {"virtualenvs": posixpath.join(ROOT_PATH, "envs"),
             "django_projects": posixpath.join(ROOT_PATH, "django"),
             "www": posixpath.join(ROOT_PATH, "www"),
             }
env.python_version = "2.6"
env.hosts = []

@runs_once
def sampleserver():
    """A sample server."""
    env.hosts.append("sample.server.com:8022")
    env.user = "username"

@runs_once
def get_details():
    """Request details for the project."""
    if not hasattr(env, "short_name"):
        env.short_name = prompt("Project's short name:")

def virtualenv():
    """Set up a virtualenv for the project."""

    get_details()

    # Set up the virtualenv.
    with cd(env.paths["virtualenvs"]):
        run("virtualenv --no-site-packages %s" % env.short_name)
        run("pip -qE %s install django" % env.short_name)


def wsgi():
    """Create the django wsgi file."""

    get_details()

    site_dir = posixpath.join(env.paths["www"], env.short_name)
    if not exists(site_dir):
        run("mkdir -p %s" % site_dir)

    filename = "django.wsgi"

    context = {"project_shortname": env.short_name,
               "python_version": env.python_version,
               "paths": env.paths,
               }

    # Set up the wsgi dir.
    with cd(site_dir):
        if not exists(filename):
            upload_template("django-wsgi-template.txt",
                            filename,
                            context,
                            use_jinja=True)
        else:
            print "This file already exists."
            return
        run("chmod +x %s" % filename)
        admin_media = posixpath.join(env.paths["virtualenvs"],
                                     env.short_name,
                                     "lib/python%s/site-packages/django/contrib/admin/media" % env.python_version)
        run("ln -s %s admin-media" % admin_media)

def apache():
    """Add a django config file in apache."""

    get_details()

    env.site_domain = prompt("Site's domain:")

    context = {"project_shortname": env.short_name,
               "paths": env.paths,
               "domain": env.site_domain,
               }

    with cd("/etc/apache2/sites-available/"):
        if not exists(env.short_name):
            upload_template("apache-django-template.txt",
                            env.short_name,
                            context,
                            use_jinja=True,
                            use_sudo=True)
        else:
            print "Apache conf file already exists."
            return

        sudo("chmod 644 %s" % env.short_name)
        sudo("a2ensite %s" % env.short_name)
        sudo("apache2ctl restart")
