from boto.s3.connection import S3Connection
import time
import subprocess
import os
from optparse import OptionParser
from types import ModuleType

DEFAULT_TEMPLATE = 'https://github.com/suneel0101/django-foundation/archive/master.zip'
EMAILER_TEMPLATE = "https://github.com/suneel0101/django-emailer/archive/master.zip"
REDIS_REPO_NAME_AND_URL = ('django-pal-redis-helper', "git://github.com/suneel0101/django-pal-redis-helper.git")


def run(*args, **kwargs):
    subprocess.call(*args, shell=True, **kwargs)


def is_settings_variable(settings, var_name):
    """
    All of the accessible variables in settings will
    be precisely those that are not of the form __*__
    """
    is_builtin = var_name.startswith("__") and var_name.endswith("__")
    is_module = type(getattr(settings, var_name)) is ModuleType
    return not is_builtin and not is_module


def get_lines_from_file(path):
    f = open(path, 'r+')
    lines = [line for line in f]
    f.close()
    return lines


def rewrite_file(path, lines):
    f = open(path, 'r+')
    for line in lines:
        f.write(line)
    f.close()


def create_directory(path):
    """
    Will create the directory if it doesn't already exist.
    """
    if not os.path.exists(path):
        run("mkdir {}".format(path))


class CodeLiteral(object):
    """
    Code stored as a string
    When written to a file, should not be escaped as a string
    but should be written as regular python code.
    """
    def __init__(self, content):
        self.content = content

    def __str__(self):
        return self.content


class ProjectHelper(object):
    def generate(self):
        (options, args) = self.get_options_and_args()

        self.template = options.template or DEFAULT_TEMPLATE
        self.name = options.name
        self.destination = self.normalize_destination(options.path)
        self.full_destination = "{}{}".format(self.destination, self.name)
        create_directory(self.destination)
        create_directory(self.full_destination)

        self.prepare()
        self.create_project()

        # Add-ons
        env_vars = {}
        if options.emailer or options.all:
            self.add_emailer()
        if options.compass or options.all:
            self.add_compass()
        if options.redis or options.all:
            self.create_app('util')
            self.add_redis()
        if options.newrelic or options.all:
            self.add_newrelic()
        if options.aws or options.all:
            if not (options.aws_id and options.aws_key):
                raise ValueError("Must set --awsid and --awskey to your AWS ID and AWS SECRET KEY, respectively")
            bucket_name = self.add_aws(options.aws_id, options.aws_key)
            env_vars.update({
                'AWS_ACCESS_KEY_ID': options.aws_id,
                'AWS_SECRET_ACCESS_KEY': options.aws_key,
                'AWS_BUCKET_NAME': bucket_name,
            })
        # Change directory into newly created project directory
        os.chdir(self.full_destination)
        options_dict = {
            'emailer': options.emailer,
            'compass': options.compass,
            'redis': options.redis,
            'newrelic': options.newrelic,
            'all': options.all,
        }

        self.deploy(env_vars=env_vars, **options_dict)

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
        parser.add_option("-t", "--template", dest="template",
                          action="store", type="string",
                          help="project template path or URL")
        parser.add_option("-e", "--emailer", dest="emailer",
                          action="store_true",
                          help="add the emailer app")
        parser.add_option("-c", "--compass", dest="compass",
                          action="store_true",
                          help="add compass")
        parser.add_option("-r", "--redis", dest="redis",
                          action="store_true",
                          help="add redis")
        parser.add_option("-w", "--newrelic", dest="newrelic",
                          action="store_true",
                          help="add newrelic")
        parser.add_option("-a", "--all", dest="all",
                          action="store_true",
                          help="add all addons")
        parser.add_option("-s", "--aws", dest="aws",
                          action="store_true",
                          help="add AWS S3 integration for static assets")
        parser.add_option("-i", "--awsid", dest="aws_id",
                          action="store", type="string",
                          help="AWS ID")
        parser.add_option("-k", "--awskey", dest="aws_key",
                          action="store", type="string",
                          help="AWS SECRET KEY")

        return parser.parse_args()

    def normalize_destination(self, destination):
        """
        If destination is entered without a trailing slash,
        append a trailing slash.
        """
        if destination[-1] != '/':
            destination = "{}/".format(destination)
        return destination

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

    def create_app(self, app_name):
        """
        Creates app named `app_name` under apps/ unless it already exists.
        """
        app_destination = '{}/apps/{}'.format(self.full_destination, app_name)
        if not os.path.exists(app_destination):
            run('mkdir {}'.format(app_destination))
            run('touch {}/__init__.py'.format(app_destination))
            self.add_installed_app(app_name)
        else:
            print "Can't create {} because it already exists!".format(
                app_destination)

    def add_to_app(self, app_name, repo_name_and_url, paths):
        """
        Adds files from any arbitrary repo to an existing app
        within your project.
        """
        if os.path.exists("{}/apps/{}".format(
                self.full_destination,
                app_name)):
            name, url = repo_name_and_url
            run("git clone {}".format(url))
            for path in paths:
                relative_path = "{}/{}".format(name, path)
                run("cp {} {}/apps/{}/{}".format(
                        relative_path,
                        self.full_destination,
                        app_name,
                        path))
            run("rm -rf {}".format(name))
        else:
            print "Can't add to app {} because it doesn't exist!".format(app_name)

    def add_redis(self):
        self.add_to_app(
            app_name='util',
            repo_name_and_url=REDIS_REPO_NAME_AND_URL,
            paths=['rediz.py'])
        imports = ['import os']
        self.add_imports(imports)
        redis_settings = {'REDIS_CONNECTION': CodeLiteral("os.environ.get('REDISTOGO_URL')")}
        self.add_to_settings(redis_settings)
        self.add_requirement('redis==2.6.2')

    def add_aws(self, aws_id, aws_secret_key):
        """
        AWS S3 ntegration on production for serving media
        """
        conn = S3Connection(aws_id, aws_secret_key)
        bucket_name = "{}-{}".format(self.name, time.time())
        conn.create_bucket(bucket_name)
        self.add_imports(['import os'], env='production')
        aws_settings = {
            'AWS_ACCESS_KEY_ID': CodeLiteral("os.environ.get('AWS_ACCESS_KEY_ID')"),
            'AWS_SECRET_ACCESS_KEY': CodeLiteral("os.environ.get('AWS_SECRET_ACCESS_KEY')"),
            'AWS_BUCKET_NAME': CodeLiteral("os.environ.get('AWS_BUCKET_NAME')"),
            'MEDIA_URL': CodeLiteral("'http://s3.amazonaws.com/{}/'.format(AWS_BUCKET_NAME)"),
            'DATABASES': CodeLiteral("{'default': dj_database_url.config(default='postgres://localhost')}"),
        }
        self.add_to_settings(aws_settings, env='production')
        return bucket_name

    def add_newrelic(self):
        self.add_requirement('newrelic==1.1.0.192')
        procfile_path = '{}/Procfile'.format(self.full_destination)
        rewrite_file(
            procfile_path,
            ["web: newrelic-admin run-program python manage.py run_gunicorn -b 0.0.0.0:\$PORT"])

    def add_emailer(self):
        """
        Adds django-emailer as `emailer` under apps.
        Adds `emailer` to INSTALLED_APPS in settings
        Adds Sendgrid Heroku addon and adds the appropriate
        Settings variables.
        """
        emailer_destination = '{}/apps/emailer'.format(self.full_destination)
        run('mkdir {}'.format(emailer_destination))
        run('django-admin.py startapp emailer {} --template={}'.format(
                emailer_destination, EMAILER_TEMPLATE))
        self.add_installed_app('emailer')
        imports = ['import os']
        self.add_imports(imports)
        emailer_config_vars = {
            'EMAIL_PORT': 587,
            'EMAIL_USE_TLS': True,
            'EMAIL_HOST': 'smtp.sendgrid.net',
            'EMAIL_HOST_USER': CodeLiteral("os.environ.get('SENDGRID_USERNAME')"),
            'EMAIL_HOST_PASSWORD': CodeLiteral("os.environ.get('SENDGRID_PASSWORD')"),
        }
        self.add_to_settings(emailer_config_vars)

    def add_compass(self):
        """
        Creates ./media folder
        Creates compass project under ./media
        """
        original_cwd = os.getcwd()
        media_destination = "{}/media".format(self.full_destination)
        run("mkdir {}".format(media_destination))
        os.chdir(media_destination)
        run("compass create --sass-dir 'sass' --css-dir 'css'")
        os.chdir(original_cwd)
        os.chdir(self.full_destination)
        run("gem install compass_twitter_bootstrap")

        # Add import to screen.scss
        compass_import = '@import "compass_twitter_bootstrap";'
        scss_path = '{}/media/sass/screen.scss'.format(self.full_destination)
        scss_lines = get_lines_from_file(scss_path)
        scss_lines.append("{}\n".format(compass_import))
        rewrite_file(scss_path, scss_lines)

        # Add require to config.rb
        config_require = "require 'compass_twitter_bootstrap'"
        config_path = '{}/media/config.rb'.format(self.full_destination)
        config_lines = get_lines_from_file(config_path)
        config_lines = ["{}\n".format(config_require)] + config_lines
        rewrite_file(config_path, config_lines)

        # Return to original directory before exiting
        os.chdir(original_cwd)

    def get_current_settings(self, env):
        """
        Reads the common settings file and
        gets all the settings variable names and values.
        """

        settings_path = '{}/settings/{}.py'.format(self.full_destination, env)
        f = open(settings_path, 'r+')
        run("cp {} .".format(settings_path))
        # g = open('temp_settings.py', 'w+')
        import_statements = []
        for line in f:
            # Extract import statements
            if 'import' in line:
                import_statements.append(line.strip())
        f.close()

        run("rm {}.pyc".format(env))
        if env == 'common':
            import common
            reload(common)
            settings_module = common
        elif env == 'production':
            import production
            reload(production)
            settings_module = production

        var_names = [x for x in dir(settings_module) if is_settings_variable(settings_module, x)]
        var_dict = {x: getattr(settings_module, x) for x in var_names}
        run("rm {}.py".format(env))
        var_dict['import_statements'] = import_statements
        return var_dict

    def add_imports(self, imports, env='common'):
        settings_dict = self.get_current_settings(env=env)
        settings_dict['import_statements'] = list(
            set(settings_dict['import_statements'] + imports))
        self.rewrite_settings(settings_dict, env=env)

    def add_installed_app(self, app_name, env='common'):
        """
        Adds `app_name` to INSTALLED_APPS in settings.common
        """
        var_dict = self.get_current_settings(env=env)
        installed_apps = var_dict['INSTALLED_APPS']
        if app_name not in installed_apps:
            var_dict['INSTALLED_APPS'] = installed_apps + (app_name,)
        self.rewrite_settings(var_dict, env=env)

    def rewrite_settings(self, settings_dict, env):
        """
        Completely Rewrites settings with the variables and
        their values from settings_dict.
        """
        h = open('{}/settings/{}.py'.format(self.full_destination, env), 'w+')
        import_statements = settings_dict['import_statements']
        del settings_dict['import_statements']
        settings_dict.keys().sort()

        for s in import_statements:
            h.write("{}\n".format(s))

        for x in sorted(settings_dict.keys()):
            y = settings_dict[x]
            # Extra quote so the string is written as a string
            # in the python file, not as python code.
            if isinstance(y, str):
                y = "'{}'".format(y)
            line_to_write = "{} = {}\n\n".format(x, y)
            print line_to_write
            h.write(line_to_write)
        h.close()

    def add_to_settings(self, settings_dict, env='common'):
        """
        Adds variables and their values in settings_dict
        as settings variables in settings.common
        """
        current_settings = self.get_current_settings(env=env)
        current_settings.update(settings_dict)
        self.rewrite_settings(current_settings, env=env)

    def add_requirement(self, requirement):
        """
        Add a requirement to the end of requirements.txt
        """
        requirements_path = "{}/requirements.txt".format(self.full_destination)
        lines = get_lines_from_file(requirements_path)
        lines.append("{}\n".format(requirement))
        rewrite_file(requirements_path, lines)

    def deploy(self, *args, **kwargs):
        """
        Initialize a git repo.
        Create a Heroku app.
        Push to Heroku.
        Scale the web process.
        """
        _all = kwargs.get('all')
        run('git init')
        run('heroku create')

        # Compile scss
        if kwargs.get('compass') or _all:
            run("compass compile media")

        run("git add . && git commit -m 'pushing to heroku'")
        run("git push heroku master")

        # Scale web process
        run("heroku ps:scale web=1")

        # Add POSTGRESQL database
        run("heroku addons:add heroku-postgresql:dev")

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

        # Add Sendgrid
        if kwargs.get('emailer') or _all:
            run("heroku addons:add sendgrid:starter")

        # Add Redis To Go
        if kwargs.get('redis') or _all:
            run("heroku addons:add redistogo:nano")

        # Add NewRelic Standard
        if kwargs.get('newrelic') or _all:
            run("heroku addons:add newrelic:standard")

        env_vars = kwargs.get('env_vars', {})
        for k, v in env_vars.iteritems():
            run("heroku config:set {}={}".format(k, v))

        # Sync to S3
        if kwargs.get('aws') or _all:
            run("heroku run python manage.py sync_media_s3")

        # Open app in browser
        run("heroku open")

if __name__ == "__main__":
    ProjectHelper().generate()
