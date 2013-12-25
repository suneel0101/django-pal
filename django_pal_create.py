from boto.s3.connection import S3Connection
import time
import subprocess
import os
from optparse import OptionParser

TEMPLATE = 'https://github.com/suneel0101/django-foundation/archive/master.zip'


def run(*args, **kwargs):
    subprocess.call(*args, shell=True, **kwargs)


def create_directory(path):
    """
    Will create the directory if it doesn't already exist.
    """
    if not os.path.exists(path):
        run("mkdir {}".format(path))


class ProjectHelper(object):
    def generate(self):
        (options, args) = self.get_options_and_args()

        self.name = options.name
        self.destination = self.normalize_destination(options.path)
        self.full_destination = "{}{}".format(self.destination, self.name)

        # Create directories
        create_directory(self.destination)
        create_directory(self.full_destination)

        # Create the prject based on the template
        self.create_project()

        # Change directory into newly created project directory
        os.chdir(self.full_destination)

        # Deploy to Heroku
        self.deploy()

    def get_options_and_args(self):
        """
        Get options and arguments from command line.
        """
        usage = "usage: %prog --path=PATH_TO_PROJ --name=PROJ_NAME"
        parser = OptionParser(usage)
        parser.add_option("-p", "--path", dest="path",
                          action="store", type="string",
                          help="project path")
        parser.add_option("-n", "--name", dest="name",
                          action="store", type="string",
                          help="project name")
        return parser.parse_args()

    def normalize_destination(self, destination):
        """
        If destination is entered without a trailing slash,
        append a trailing slash.
        """
        if destination[-1] != '/':
            destination = "{}/".format(destination)
        return destination

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
                TEMPLATE, self.name, self.full_destination))
        run('touch {}/settings/active.py'.format(
                self.full_destination, self.name))

    def add_s3_bucket(self):
        """
        AWS S3 ntegration on production for serving media
        """
        conn = S3Connection(
            os.environ.get("AWS_ACCESS_KEY_ID"),
            os.environ.get("AWS_SECRET_ACCESS_KEY"))

        bucket_name = "{}-{}".format(self.name, time.time())
        conn.create_bucket(bucket_name)
        return bucket_name

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

        # Scale web process
        run("heroku ps:scale web=1")

        # Promote database so DATABASE_URL is set
        x = subprocess.Popen(["heroku config | grep HEROKU_POSTGRESQL"],
                             shell=True,
                             stdout=subprocess.PIPE)
        postgres_url_info = x.communicate()[0]
        heroku_postgres_url = postgres_url_info.split(":")[0]
        run("heroku pg:promote {}".format(heroku_postgres_url))

        # Sync and migrate db
        run("heroku run python manage.py syncdb")
        run("heroku run python manage.py migrate")

        # Add Sentry
        run("heroku addons:add sentry:developer")

        bucket_name  = self.add_s3_bucket()

        env_vars = {
            "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "AWS_BUCKET_NAME": bucket_name,
        }

        for k, v in env_vars.iteritems():
            run("heroku config:set {}={}".format(k, v))

        # Sync to S3
        run("heroku run python manage.py sync_media_s3")

        # Open app in browser
        run("heroku open")

if __name__ == "__main__":
    ProjectHelper().generate()
