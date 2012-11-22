import os
from optparse import OptionParser
from subprocess import call


def run(*args, **kwargs):
    call(*args, shell=True, **kwargs)


class Command(object):
    def main(self):

        usage = "usage: %prog --path=PATH_TO_PROJ --name=PROJ_NAME"
        parser = OptionParser(usage)
        parser.add_option("-p", "--path", dest="path",
                          action="store", type="string",
                          help="project path")
        parser.add_option("-n", "--name", dest="name",
                          action="store", type="string",
                          help="project name")
        parser.add_option("-t", "--template", dest="template",
                          action="store", type="string",
                          help="project template path or URL")
        parser.add_option("-e", "--emailer", dest="emailer",
                          action="store_true",
                          help="add the emailer app")


        (options, args) = parser.parse_args()

        DEFAULT_TEMPLATE = 'https://github.com/suneel0101/django-foundation/archive/master.zip'
        self.template = options.template or DEFAULT_TEMPLATE
        self.name = options.name
        self.destination = options.path

        # If destination is entered without a trailing slash
        # Append a trailing slash
        if self.destination[-1] != '/':
            self.destination = "{}/".format(self.destination)
        self.full_destination = "{}{}".format(self.destination, self.name)

        self.prepare()
        self.create_project()
        if options.emailer:
            self.add_emailer()
        # Change directory into newly created project directory
        os.chdir(self.full_destination)
        #self.deploy()

    def prepare(self):
        """
        Grab django project template
        Create a virtual environment
        Activate virtual environment
        Install Django
        """
        run('virtualenv venv --distribute')
        run('source venv/bin/activate')
        run('pip install django')

    def create_project(self):
        """
        Create Django project according to `template` at `destination`
        with project name `name`
        Create active.py, which will be git ignored
        """
        original_cwd = os.getcwd()
        os.chdir(self.destination)
        run('mkdir {}'.format(self.name))
        os.chdir(original_cwd)
        run(u'django-admin.py startproject --template={} {} {}'.format(
                self.template, self.name, self.full_destination))
        run('touch {}/settings/active.py'.format(
                self.full_destination, self.name))

    def add_emailer(self):
        EMAILER_TEMPLATE = "https://github.com/suneel0101/django-emailer/archive/master.zip"
        emailer_destination = '{}/apps/emailer'.format(self.full_destination)
        run('mkdir {}'.format(emailer_destination))
        run('django-admin.py startapp emailer {} --template={}'.format(
                emailer_destination, EMAILER_TEMPLATE))

    def deploy(self):
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
        run("heroku run python manage.py syncdb")
        run("heroku run python manage.py migrate")
        run("heroku open")

if __name__ == "__main__":
    Command().main()
