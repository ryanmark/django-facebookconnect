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
log = logging.getLogger('facebookconnect.middleware')
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

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

class FacebookConnectMiddleware(object):
    """Middlware to provide a working facebook object"""
    def process_request(self,request):
        """process incoming request"""
        
        # clear out the storage of fb ids in the local thread
        if hasattr(_thread_locals,'fbids'):
            del _thread_locals.fbids
        
        try:
            # This is true if anyone has ever used the browser to log in to
            # facebook with an acount that has accepted this application.
            bona_fide = request.facebook.check_session(request)
            uid = request.facebook.uid
            log.debug("Bona Fide: %s, Logged in: %s" % (bona_fide, uid))
            
            if bona_fide and uid:
                user = request.user
                if user.is_anonymous():
                    # user should be in setup
                    setup_url = reverse('facebook_setup')
                    if request.path != setup_url:
                        request.facebook.session_key = None
                        request.facebook.uid = None
            else:
                # we have no fb info, so we shouldn't have a fb only
                # user logged in
                user = request.user
                if user.is_authenticated() and bona_fide:
                    try:
                        fbp = FacebookProfile.objects.get(user=user)
                    
                        if fbp.facebook_only():
                            cur_user = request.facebook.users.getLoggedInUser()
                            if int(cur_user) != int(request.facebook.uid):
                                logout(request)
                                request.facebook.session_key = None
                                request.facebook.uid = None
                    except FacebookProfile.DoesNotExsist, ex:
                        # user doesnt have facebook :(
                        pass
            
        except Exception, ex:
            # Because this is a middleware, we can't assume the errors will 
            # be caught anywhere useful.
            logout(request)
            request.facebook.session_key = None
            request.facebook.uid = None
            log.exception(ex)
    
        return None
    
    def process_exception(self,request,exception):
        my_ex = exception
        if type(exception) == TemplateSyntaxError:
            if getattr(exception,'exc_info',False):
                my_ex = exception.exc_info[1]

        if type(my_ex) == FacebookError:
            # we get this error if the facebook session is timed out
            # we should log out the user and send them to somewhere useful
            if my_ex.code is 102:
                logout(request)
                request.facebook.session_key = None
                request.facebook.uid = None
                log.error('102, session')
                return HttpResponseRedirect(reverse('facebookconnect.views.facebook_login'))
        elif type(my_ex) == URLError:
            if my_ex.reason is 104:
                log.error('104, connection reset?')
            elif my_ex.reason is 102:
                log.error('102, name or service not known')
