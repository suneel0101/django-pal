## Purpose

django_pal_create.py is a command which generates and deploys a starter Django application to Heroku.
The project template is based on http://github.com/suneel0101/django-foundation, but you can pass in any arbitrary django
project template through the --template option.

It also gives you the option of automatically integrating thirdparty services such as Sendgrid, RedisToGo, NewRelic, S3 and Compass (with Twitter Bootstrap).

python django_pal_create.py requires the following parameters

`--path`: (String) path to the directory where you want your application to be created
`--name`: (String) name of the project

Sample usage:

`python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app"`

Specifying your own template:

```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --template="http://github.com/suneelius/other-template/archive/master.zip"
```


## Instructions to Create and Deploy

1. `git clone git://github.com/suneel0101/django-pal.git && cd django-pal`
2. `python django_pal_create.py --path="/path/to/proj/directory/" --name="your-project-name"`

Now, your application is deployed to Heroku. Now, setup your local development enviornment:

3. `cd /path/to/proj/directory`
4. `virtualenv venv --distribute && . venv/bin/activate`
5. `make`

Step 5 will install requirements within your virtualenv and sync and migrate the database. Finally, it will runserver.

## Addons

On how to integrate the third party services:

### 1. Sendgrid and emailer application

Pass the following parameter into the command: `--emailer`

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --emailer
```

This will add an emailer app under the main project “apps” folder which is a clone of https://github.com/suneel0101/django-emailer. Also, on the live site through Heroku, it will also add the free Sendgrid starter package with the appropriate variables automatically added to the settings files.

You can use this base emailer application, which provides a BaseEmailEngine, to create an email engine for your own purpose. Here is an example:

```python
class WelcomeEmail(BaseEmailEngine):
       '''
       A welcome email once a user signs up for our service.
       '''
       template = 'welcome.html'
       def __init__(self, user):
           self.user = user
       def get_recipients(self):
           return [self.user.email]

   >>> from emailer import WelcomeEmail
   >>> first_user = User.objects.get(id=1)
   >>> WelcomeEmail(first_user).send()
```

### 2. Redis

Pass the following parameter into the command: `--redis`

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --redis
```

This will add a file under `apps/util` called `rediz.py` that has some basic and useful helpers for Redis usage and will also spin up a RedisToGo (the nano free version) instance and connect it to your app, with the appropriate settings files updated with the redis variables.

### 3. New Relic

To automatically add free NewRelic analytics tracking to your live site, just pass the the following parameter to the command: 
`--newrelic`

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --emailer --newrelic
```

### 4. Compass

For easy style management, integrated with a compass version of Twitter Bootstrap (https://github.com/vwall/compass-twitter-bootstrap), add the following parameter to the command:
`--compass`

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --emailer --newrelic --compass
```

### 5. S3 static asset hosting

Ideally in production you don’t want your static assets to be served by the django server. Instead you want it served from somewhere else. The standard is S3.

This will create a bucket, upload your static assets to it and your live site will be configured to serve static assets from S3 by setting the appropriate settings variables. You don’t have to worry about the pain or hassle of doing this manually. You just have to do is pass in all the following parameters:

`--aws (no value)`
`--awsid (String): AWS ID`
`--awskey (String): AWS Secret Key`

Your AWS ID and Secret Key can be found in your account credentials section after logging into aws.amazon.com

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --aws --awsid="my_aws_id_982349872" --awskey="my_aws_secret_key_sd987sdf"
```

### 6. All

If you want all the above, you just pass in the following parameters:
`--all`
`--awsid (String)`
`--awskey (string)`

Sample usage:
```
python django_pal_create.py --path="/Users/suneel0101/Development/" --name="sample_app" --all --awsid="my_aws_id_982349872" --awskey="my_aws_secret_key_sd987"
```

## Rolling Out after the First Time:

After you create your project and roll out for the first time, when you make changes and want to make another release, all you have to do is run the following command:

```
python manage.py rollout
```

This will upload your static assets to S3 and then push your latest commit to Heroku. Feel free to beef up this command with your own personal needs!

## Dependencies

1. Heroku account and toolbelt
2. git
3. pip
