# from https://github.com/SeanHayes/django-facebook-oauth

from datetime import datetime
import pdb
from django.conf import settings
import facebook
import urllib,urllib2

from django.contrib.auth.models import User
from models import FacebookProfile

from django.contrib.auth.backends import ModelBackend
from django.core.urlresolvers import reverse
APP_ID = settings.FACEBOOK_APP_ID
APP_SECRET = settings.FACEBOOK_SECRET_KEY
import logging
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FbAuth(ModelBackend):
    """
    Authenticate against the Facebook Authentication

    Use the login name, and a hash of the password. For example:
    """

    def authenticate(self, verification_code=None, cookies=[]):
        access_token = None
        fb_profile = None
        if(cookies):
            access_token = facebook.get_user_from_cookie(cookies, APP_ID, APP_SECRET)
            if 'fbs_' + APP_ID in cookies and datetime.fromtimestamp(float(access_token['expires'])) > datetime.now():
                graph = facebook.GraphAPI(access_token['access_token'])
                fb_profile = graph.get_object('me')

            id = access_token['uid']

        elif verification_code:
            url = 'http://%s%s' % (settings.HOST, reverse('fb_auth'))
            logger.debug(url)

            args = dict(client_id=APP_ID, redirect_uri=url)
            args["client_secret"] = APP_SECRET
            args["code"] = verification_code
            logger.debug(args)

            url = "https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args)
            logger.debug('Access Token URL: %s' % url)
            try:
                response = urllib2.urlopen(url).read()
                logger.debug('response: %s' % response)
                atoken = response.split('&')[0].split('=')[-1]
                access_token = urllib.unquote(atoken)

                graph = facebook.GraphAPI(access_token)
                fb_profile = graph.get_object('me')
                id = fb_profile['id']
            except Exception as e:
                logger.exception(e)

        if(fb_profile):
            #logger.debug('fb_profile: %s' % fb_profile)
            if type(access_token) == dict:
                access_token = access_token['access_token']
            logger.debug('Access Token: %s' % access_token)
            fb_user = self.updateDb(fb_profile, access_token)
            logger.debug('FB User: %s' % fb_user)
            return fb_user.user
        else:
            return None

    def updateDb(self, fb_profile, access_token):
        #logger.debug(fb_profile)
        #logger.debug('Access Token: %s' % access_token)
        #check if user is an app admin/developer
        is_admin = False
        try:
            #returns a list of apps the user is a dev of
            url = 'https://api.facebook.com/method/fql.query?format=json&query=SELECT%%20application_id%%20FROM%%20developer%%20WHERE%%20developer_id%%20=%%20%s&access_token=%s' % (fb_profile['id'], access_token)

            apps = json.loads(urllib2.urlopen(url).read())

            for app in apps:
                if app['application_id'] == APP_ID:
                    is_admin = True
                    break
        except Exception as e:
            logger.error(e)
        logger.debug('Admin status: %s' % is_admin)

        try:
            fb_user = FacebookProfile.objects.get(facebook_id=fb_profile['id'])

            #update access token if it's changed
            if fb_user.access_token is not access_token:
                fb_user.access_token = access_token
                fb_user.save()

            #TODO: decide whether to use the following try/catch from upstream or stick with previous 3 lines
            #update access token if old one doesn't work
            #try:
            #	graph = facebook.GraphAPI(fb_user.access_token)
            #	graph = graph.get_object('me')
            #except Exception,e:
            #	fb_user.access_token = access_token
            #	fb_user.save()

            user = fb_user.user

            #save if either value has changed
            if user.is_staff is not is_admin or user.is_superuser is not is_admin:
                user.is_staff = is_admin
                user.is_superuser = is_admin
                user.save()

        except FacebookProfile.DoesNotExist as e:
            logger.debug('%s' % e)
            try:
                email = fb_profile['email']
            except:
                email = fb_profile['id'] + '@dummyfbemail.com'

            username = fb_profile['name']

            #we need a unique User created. Otherwise another user might be able
            #to change his or her username to someone else's FB ID, thereby causing
            #this script to crash and preventing that FB user from registering.
            unique = False
            while not unique:
                try:
                    User.objects.get(username=username)
                    d = datetime.now()
                    username = re.sub(r'[-:.]', '', d.isoformat())
                except User.DoesNotExist:
                    unique = True

            user = User(
                    username=username,
                    email=email,
                    first_name=fb_profile['first_name'],
                    last_name=fb_profile['last_name'])
            user.set_unusable_password()
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save()

            fb_user = FacebookUser(
                    user=user,
                    uid=str(fb_profile["id"]),
                    name=fb_profile["name"],
                    access_token=access_token,
                    url=fb_profile["link"])
            fb_user.save()

        return fb_user


