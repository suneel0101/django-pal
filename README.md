Django-Pal
==========
Django-Pal does two things.

1. It creates a Django project based on the Django project template in http://github.com/suneel0101/django-foundation.
2. Then, it deploys to Heroku.

All the code is in the create.py script. It's very straightforward, so please take a look and it will all be clear to you.

Instructions
===========

1. `git clone git://github.com/suneel0101/django-pal.git && cd django-pal`
2. `python create.py --path="/path/to/proj/directory/" --name="your-project-name"`

Now, your application is deployed to Heroku. Now, setup your local development enviornment:

3. `cd /path/to/proj/directory`
4. `virtualenv venv --distribute && . venv/bin/activate`
5. `make`

Step 5 will install requirements within your virtualenv and sync and migrate the database. Finally, it will runserver.

Dependencies
============

1. Heroku account and toolbelt
2. git
3. pip