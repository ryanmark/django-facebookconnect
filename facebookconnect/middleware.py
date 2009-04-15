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

import logging
import warnings
from datetime import datetime
from django.core.urlresolvers import reverse
from django.contrib.auth import logout,login
from django.conf import settings
from facebook import Facebook,FacebookError
from django.template import TemplateSyntaxError
from django.http import HttpResponseRedirect,HttpResponse
from urllib2 import URLError
from facebookconnect.models import FacebookProfile

class FacebookConnectMiddleware(object):
    """Middlware to provide a working facebook object"""
    def process_request(self,request):
        """process incoming request"""
        try:
            # this is true if anyone has ever used the browser to log in to facebook with an acount
            # that has accepted this application. useless.
            bona_fide = request.facebook.check_session(request)
            logging.debug("FBC Middleware: UID in request: %s" % request.facebook.uid)
            
            logging.debug("FBC Middleware: Bona Fide: %s, Logged in: %s, Session: %s" % (bona_fide,request.facebook.uid,request.facebook.session_key))
            
            # make sure a users django auth and facebook auth are in sync, if they are 
            # a facebook only user
            if (request.user.is_authenticated() 
                    and request.user.facebook_profile 
                    and request.user.facebook_profile.facebook_only()):
                cur_user = request.facebook.users.getLoggedInUser()
                if not bona_fide or int(cur_user) != int(request.facebook.uid):
                    logging.debug("FBC Middleware: DIE DIE DIE")
                    logout(request)
                    request.facebook.session_key = None
                    request.facebook.uid = None

        except FacebookProfile.DoesNotExist,ex:
            logging.debug(u"FBC Middleware: User doesn't have facebook or needs to finish setup!")
        except Exception, ex:
            #Because this is a middleware, we can't assume the errors will be caught elsewhere.
            logout(request)
            request.facebook.session_key = None
            request.facebook.uid = None
            warnings.warn(u'FBC Middleware failed: %s' % ex)
            logging.exception('FBC Middleware: something went terribly wrong')
    
    def process_exception(self,request,exception):
        my_ex = exception
        if type(exception) == TemplateSyntaxError:
            if getattr(exception,'exc_info',False):
                my_ex = exception.exc_info[1]

        if type(my_ex) == FacebookError:
            if my_ex.code is 102:
                logout(request)
                request.facebook.session_key = None
                request.facebook.uid = None
                logging.error('FBC middleware: 102, session')
                return HttpResponseRedirect(reverse('authentication.views.facebook_login'))
        elif type(my_ex) == URLError:
            if my_ex.reason is 104:
                logging.error('FBC middleware: 104, connection reset?')
            elif my_ex.reason is 102:
                logging.error('FBC middleware: 102, name or service not known')
