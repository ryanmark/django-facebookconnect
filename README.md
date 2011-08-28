WARNING: THIS THING IS OBSOLETE - DON'T USE IT

Use this one instead: http://github.com/ryanmark/django_facebook_oauth

This thing uses an old hacky way of doing authentication that Facebook has deprecated. Do yourself a favor and use OAUTH and Facebook's Open Graph API. It's sooooo much better.


django-facebookconnect
======================

Copyright 2009 Ryan Mark


Intro
-----

*django-facebookconnect* extends the builtin Django auth system to let your visitors use thier Facebook account to log into your site. It works with existing user accounts and django-registration (although django-registration isn't required). Your visitors can still use their Django username and password, or they can log in with their Facebook account and link it to their existing django user account. If they don't have an existing user account, they can login with facebook and a dummy django Uuser will get setup for them seamlessly.

Installation
------------

I'm dumping the code for the first rev into source control. Just pull it out with svn and put the facebookconnect directory somewhere in your python path. Either in your application with your other apps, or in your python site-packages directory.

Make sure you have [pyfacebook](http://github.com/sciyoshi/pyfacebook/tree/master) installed. You can get code and instructions on github: http://github.com/sciyoshi/pyfacebook/tree/master

django-facebookconnect only requires the stock Django auth app, but it also plays nice with django-registration if you would like to give your users the option to log in without Facebook.

Add facebookconnect and django auth to your `INSTALLED_APPS`:

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.sessions',

        'facebookconnect',
    )

Both pyfacebook and django-facebookconnect have middleware that needs to be used. Middleware is a funny thing and is sensitive to the order in which it is executed. This order works:

    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'facebook.djangofb.FacebookMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'facebookconnect.middleware.FacebookConnectMiddleware',
    )

If you have other middleware, you may have to experiment with where in the list you should put your middleware. If you change the order of the stuff above, it will break.

Add the facebook to your authentication backends. If you dont have an `AUTHENTICATION_BACKENDS` directive in your settings, just use this one:

    AUTHENTICATION_BACKENDS = (
        'facebookconnect.models.FacebookBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

One more thing you may want to know about is the dummy facebook data. If, for whatever reason, the code can't retrieve facebook profile information for a user, it will use dummy data. Facebook Connect drops requests from time to time, so instead of killing the application, it will just show something. You can set the `DUMMY_FACEBOOK_INFO` directive in the settings file to change the default stuff. Here is what the default stuff looks like:

    DUMMY_FACEBOOK_INFO = {
        'uid':0,
        'name':'(Private)',
        'first_name':'(Private)',
        'pic_square_with_logo':'http://www.facebook.com/pics/t_silhouette.gif',
        'affiliations':None,
        'status':None,
        'proxied_email':None,
    }

Facebook API
------------

Setup a Facebook applicaiton here: http://upload.facebook.com. You'll need to have a personal Facebook account to set this up. Once you add a Facebook app, go to the connect section of the setup and provide the url for your Facebook Connect site (developers can enter localhost). Once you save the settings, you get an API key and secret. In your django settings file enter this stuff:

    FACEBOOK_API_KEY = '00000000000000000000000000000000'
    FACEBOOK_SECRET_KEY = '00000000000000000000000000000000'
    FACEBOOK_INTERNAL = True

The third setting is for pyfacebook. I don't know what it does completely. But it does cause pyfacebook to hold on to expired facebook sessions when it's False.

Caching
-------

So you have to use caching with Facebook Connect. Especially if you plan to display profile info from your Facebook Connect users. Caching is used no matter what, but if you don't configure it, Django will just cache to memory for the execution and not for the long term. Or something. It's probably bad.

So read this http://docs.djangoproject.com/en/dev/topics/cache/ and setup database caching or memcached. There is one more setting directive you might be interested in:

    # Cache facebook info for x seconds. Default is 30 minutes
    FACEBOOK_CACHE_TIMEOUT = 1800

Django's cache framework rocks by the way.

Using Facebook Connect
----------------------

Once you've got everything installed, all user objects will have a `facebook_profile` attribute. That is if the user has logged in with Facebook. The `FacebookProfile` object has all sorts of nifty methods and properties.

There are templates that you can override. The setup screen is presented to a new Facebook user when they first log in. A user can then choose to link their Facebook account to an existing account or not. To get these views add the following to your project's url.py:

    urlpatterns = patterns('',
        ...,
        (r'^facebook/', include('facebookconnect.urls')),
    )

There is a template tag library called `facebook_tags` which has a bunch of shortcuts for displaying Facebook profile information for a user. Put
`{% load facebook_tags %}`
at the very top, immediately after any `{% extends %}` statement. Put
`{% facebook_js %}`
in the html head section and put
`{% initialize_facebook_connect %}`
at the bottom of your `base.html` file before the closing body tag. It will install the Facebook JavaScript and contains some JavaScript functions for publishing data to a Facebook feed. Put 
`{% show_connect_button %}`
wherever you want a "Connect with Facebook" button.

Django has a builtin `LOGIN_REDIRECT_URL` setting that django-facebookconnect uses when a user logs in with facebook. By default a user will be redirected to `/accounts/profile`. If you want this to be something different, set `LOGIN_REDIRECT_URL` in your settings file.

There is also a management command called `installfacebooktemplates`. This command loads special facebook templates from a directive in your settings file called `FACEBOOK_TEMPLATES` and stores the reference ids in the db. You can get at those templates through the `FacebookTemplate` model. See the `settings.EXAMPLE.py` file for more details on how to define Facebook templates.
