import os
from optparse import OptionParser
from subprocess import call


def run(*args, **kwargs):
    call(*args, shell=True, **kwargs)


def main():
    usage = "usage: %prog --path=PATH_TO_PROJ --name=PROJ_NAME"
    parser = OptionParser(usage)
    parser.add_option("-p", "--path", dest="path",
                      action="store", type="string",
                      help="project path")
    parser.add_option("-n", "--name", dest="name",
                      action="store", type="string",
                      help="project name")
    (options, args) = parser.parse_args()

    template = 'django-foundation'
    name = options.name
    destination = options.path

    # If destination is entered without a trailing slash
    # Append a trailing slash
    if destination[-1] != '/':
        destination = "{}/".format(destination)

    prepare()
    create_project(template, name, destination)
    # Change directory into newly created project directory
    os.chdir(destination)
    deploy()


def prepare():
    """
    Grab django project template
    Create a virtual environment
    Activate virtual environment
    Install Django
    """
    run('git clone git://github.com/suneel0101/django-foundation.git')
    run('virtualenv venv --distribute')
    run('source venv/bin/activate')
    run('pip install django')


def create_project(template, name, destination):
    """
    Create Django project according to `template` at `destination`
    with project name `name`
    Create active.py, which will be git ignored
    """
    run('django-admin.py startproject --template={} {} {}'.format(
            template, name, destination))
    full_destination = "{}{}".format(destination, name)
    run('touch {}/settings/active.py'.format(full_destination, name))


def deploy():
    """
    Initialize a git repo.
    Create a Heroku app.
    Push to Heroku.
    Scale the web process.
    """
    run('git init')
    run('heroku create')
    run("git add . && git commit -m 'pushing to heroku'")
    run("git push heroku master")
    run("heroku ps:scale web=1")
    run("heroku open")

if __name__ == "__main__":
    main()
