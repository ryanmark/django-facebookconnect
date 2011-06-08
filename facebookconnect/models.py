# Copyright 2008-2009 Brian Boyer, Ryan Mark, Angela Nitzke, Joshua Pollock,
# Stuart Tiffen, Kayla Webley and the Medill School of Journalism, Northwestern
# University.
#
# This file is part of django-facebookconnect.
#
# django-facebookconnect is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-facebookconnect is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with django-facebookconnect.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
log = logging.getLogger('facebookconnect.models')
import sha, random
from urllib2 import URLError

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_delete

class FacebookTemplate(models.Model):
    name = models.SlugField(unique=True)
    template_bundle_id = models.BigIntegerField()

    def __unicode__(self):
        return self.name.capitalize()

class FacebookProfile(models.Model):
    user = models.OneToOneField(User,related_name="facebook_profile")
    facebook_id = models.BigIntegerField(unique=True)

    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    access_token = models.CharField(max_length=500, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    img_url = models.URLField(blank=True, null=True)

    __facebook_info = None
    dummy = True

    FACEBOOK_FIELDS = ['uid,name,first_name,last_name,pic_square_with_logo,affiliations,status,proxied_email']
    DUMMY_FACEBOOK_INFO = {
        'uid': 0,
        'name': '(Private)',
        'first_name': '(Private)',
        'last_name': '(Private)',
        'pic_square_with_logo': 'http://www.facebook.com/pics/t_silhouette.gif',
        'affiliations': None,
        'status': None,
        'proxied_email': None,
    }

    def __init__(self, *args, **kwargs):
        """reset local DUMMY info"""
        super(FacebookProfile,self).__init__(*args,**kwargs)
        try:
            self.DUMMY_FACEBOOK_INFO = settings.DUMMY_FACEBOOK_INFO
        except AttributeError:
            pass
        try:
            self.FACEBOOK_FIELDS = settings.FACEBOOK_FIELDS
        except AttributeError:
            pass

    def __get_picture_url(self):
        if self.__configure_me() and self.__facebook_info['pic_square_with_logo']:
            return self.__facebook_info['pic_square_with_logo']
        else:
            return self.DUMMY_FACEBOOK_INFO['pic_square_with_logo']
    picture_url = property(__get_picture_url)
    
    def __get_full_name(self):
        if self.__configure_me() and self.__facebook_info['name']:
            return u"%s" % self.__facebook_info['name']
        else:
            return self.DUMMY_FACEBOOK_INFO['name']
    full_name = property(__get_full_name)
    
    def __get_first_name(self):
        if self.__configure_me() and self.__facebook_info['first_name']:
            return u"%s" % self.__facebook_info['first_name']
        else:
            return self.DUMMY_FACEBOOK_INFO['first_name']
    first_name = property(__get_first_name)
    
    def __get_last_name(self):
        if self.__configure_me() and self.__facebook_info['last_name']:
            return u"%s" % self.__facebook_info['last_name']
        else:
            return self.DUMMY_FACEBOOK_INFO['last_name']
    last_name = property(__get_last_name)
    
    def __get_networks(self):
        if self.__configure_me():
            return self.__facebook_info['affiliations']
        else: return []
    networks = property(__get_networks)

    def __get_email(self):
        if self.__configure_me() and self.__facebook_info['proxied_email']:
            return self.__facebook_info['proxied_email']
        else:
            return ""
    email = property(__get_email)

    def facebook_only(self):
        """return true if this user uses facebook and only facebook"""
        if self.facebook_id and str(self.facebook_id) == self.user.username:
            return True
        else:
            return False
    
    def is_authenticated(self):
        """Check if this fb user is logged in"""
        return False

    def get_friends_profiles(self,limit=50):
        '''returns profile objects for this persons facebook friends'''
        return False

    def __get_facebook_friends(self):
        """returns an array of the user's friends' fb ids"""
        return False

    def __get_facebook_info(self,fbids):
        return False

    def __configure_me(self):
        """Calls facebook to populate profile info"""
        return False

    def get_absolute_url(self):
        return "http://www.facebook.com/profile.php?id=%s" % self.facebook_id

    def __unicode__(self):
        return "FacebookProfile for %s" % self.facebook_id

def unregister_fb_profile(sender, **kwargs):
    """call facebook and let them know to unregister the user"""
    fb = get_facebook_client()
    fb.connect.unregisterUser([fb.hash_email(kwargs['instance'].user.email)])

#post_delete.connect(unregister_fb_profile,sender=FacebookProfile)
