Django-Pal
==========
Django-Pal does two things.

1. It creates a Django project based on the Django project template in http://github.com/suneel0101/django-foundation.
2. Then, it deploys to Heroku.

Instructions to Create and Deploy
===========

1. `git clone git://github.com/suneel0101/django-pal.git && cd django-pal`
2. `python create.py --path="/path/to/proj/directory/" --name="your-project-name"`

Now, your application is deployed to Heroku. Now, setup your local development enviornment:

3. `cd /path/to/proj/directory`
4. `virtualenv venv --distribute && . venv/bin/activate`
5. `make`

Step 5 will install requirements within your virtualenv and sync and migrate the database. Finally, it will runserver.

Addons
============

## Compass Project (with Twitter Bootstrap)

run the `create` command with `--compass`

This will create a compass project under media/ and will also have compass version of Twitter Bootstrap already imported into screen.scss as per https://github.com/vwall/compass-twitter-bootstrap.

## Emailer App (with automatic Sendgrid integration)

run the `create` command with `--emailer`

This will create a django-emailer app (https://github.com/suneel0101/django-emailer) called `emailer` under apps/

## Redis (with automatic Heroku Redis To Go integration)

This will add a file under apps/util called rediz.py that has some basic and useful helpers for Redis usage (https://github.com/suneel0101/django-pal-redis-helper)

Dependencies
============

1. Heroku account and toolbelt
2. git
3. pip