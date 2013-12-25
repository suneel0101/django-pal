## Purpose

django_pal_create.py is a command which generates and deploys a starter Django application to Heroku.
The project template is based on http://github.com/suneel0101/django-foundation, but you can pass in any arbitrary django
project template through the --template option.
).

## Instructions

python django_pal_create.py requires the following parameters

`--path`: (String) path to the directory where you want your application to be created

`--name`: (String) name of the project

Furthermore, you should have `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` available in the environment in which you run the `django_pal_create` command.

## Usage

`python django_pal_create.py --path="/Users/<your_user_name>/Development/" --name="<whatever_app_name_you_want>"`
