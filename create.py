import os
from optparse import OptionParser
from subprocess import call

DEFAULT_TEMPLATE = 'https://github.com/suneel0101/django-foundation/archive/master.zip'
EMAILER_TEMPLATE = "https://github.com/suneel0101/django-emailer/archive/master.zip"


def run(*args, **kwargs):
    call(*args, shell=True, **kwargs)


def is_settings_variable(var_name):
    return not (var_name.startswith("__") and var_name.endswith("__"))


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

        self.prepare()
        self.create_project()

        # Add-ons
        if options.emailer:
            self.add_emailer()
        if options.compass:
            self.add_compass()

        # Change directory into newly created project directory
        os.chdir(self.full_destination)
        #self.deploy()

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

    def get_current_settings(self):
        """
        Reads the common settings file and
        gets all the settings variable names and values.
        """
        f = open('{}/settings/common.py'.format(self.full_destination), 'r+')
        g = open('temp_settings.py', 'w+')
        import_statements = []
        for line in f:
            if 'import' in line:
                import_statements.append(line.strip())
            else:
                g.write(line)
        f.close()
        g.close()
        import temp_settings
        var_names = [x for x in dir(temp_settings) if is_settings_variable(x)]
        var_dict = {x: getattr(temp_settings, x) for x in var_names}
        run("rm temp_settings.py")
        var_dict['import_statements'] = import_statements
        return var_dict

    def add_imports(self, imports):
        settings_dict = self.get_current_settings()
        settings_dict['import_statements'] = list(
            set(settings_dict['import_statements'] + imports))
        self.rewrite_settings(settings_dict)

    def add_installed_app(self, app_name):
        """
        Adds `app_name` to INSTALLED_APPS in settings.common
        """
        var_dict = self.get_current_settings()
        if app_name not in var_dict['INSTALLED_APPS']:
            var_dict['INSTALLED_APPS'] += (app_name,)
        self.rewrite_settings(var_dict)

    def rewrite_settings(self, settings_dict):
        """
        Completely Rewrites settings with the variables and
        their values from settings_dict.
        """
        h = open('{}/settings/common.py'.format(self.full_destination), 'w+')
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
            h.write("{} = {}\n\n".format(x, y))
        h.close()

    def add_to_settings(self, settings_dict):
        """
        Adds variables and their values in settings_dict
        as settings variables in settings.common
        """
        current_settings = self.get_current_settings()
        current_settings.update(settings_dict)
        self.rewrite_settings(current_settings)

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
    ProjectHelper().generate()
