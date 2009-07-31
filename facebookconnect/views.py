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
import sha, random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.conf import settings

from facebookconnect.models import FacebookProfile

def facebook_login(request):
    if request.method == "POST":
        logging.debug("FBC: OK logging in...")
        if request.POST.get('next',False) and request.POST['next']:
            next = request.POST['next']
        else:
            next = getattr(settings,'LOGIN_REDIRECT_URL','/')
        user = authenticate(request=request)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                logging.debug("FBC: Redirecting to %s" % next)
                return HttpResponseRedirect(next)
            else:
                logging.debug("FBC: This account is disabled.")
                raise FacebookAuthError('This account is disabled.')
        elif request.facebook.uid:
            #we have to set this user up
            logging.debug("FBC: Redirecting to setup")
            return HttpResponseRedirect(reverse('facebook_setup')+"?next=%s" % next)
    
    logging.debug("FBC: Got redirected here")
    url = reverse('auth_login')
    if request.GET.get('next',False):
        url += "?next=%s" % request.GET['next']
    return HttpResponseRedirect(url)

def facebook_logout(request):
    logout(request)
    if getattr(request,'facebook',False):
        request.facebook.session_key = None
        request.facebook.uid = None
    return HttpResponseRedirect(getattr(settings,'LOGOUT_REDIRECT_URL','/'))
    
def setup(request):
    if not request.facebook.uid:
        return HttpResponseRedirect(reverse('auth_login')+"?next="+request.GET.get('next',''))
    
    if request.method == "POST":
        if request.POST.get('next',False) and request.POST['next']:
            next = request.POST['next']
        else:
            next = getattr(settings,'LOGIN_REDIRECT_URL','/')
            
        profile = FacebookProfile(facebook_id=request.facebook.uid)
        
        if request.POST.get('facebook_only',False):
            user = User(username=request.facebook.uid, 
                        password=sha.new(str(random.random())).hexdigest()[:8],
                        email=profile.email)
            user.save()
            profile.user = user
            profile.save()
            logging.info("FBC: Added user and profile for %s!" % request.facebook.uid)
            user = authenticate(request=request)
            login(request, user)
            return HttpResponseRedirect(next)
            
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            logging.debug("FBC: Trying to setup FB: %s, %s" % (user,profile))
            if user is not None and user.is_active:
                profile.user = user
                profile.save()
                logging.info("FBC: Attached facebook profile %s to user %s!" % (profile.facebook_id,user))
                login(request, user)
                return HttpResponseRedirect(next)
        else:
            user = User()
            user.facebook_profile = profile
    
    elif request.user.is_authenticated():
        profile = FacebookProfile(facebook_id=request.facebook.uid)
        profile.user = request.user
        profile.save()
        logging.info("FBC: Attached facebook profile %s to user %s!" % (profile.facebook_id,profile.user.id))
        return HttpResponseRedirect(next)
    
    else:
        user = User()
        user.facebook_profile = FacebookProfile(facebook_id=request.facebook.uid)
        next = request.GET.get('next','')
        form = AuthenticationForm(request)
        
    return render_to_response(
        'facebook/setup.html',
        {"user":user,
         "form":form,
         "next":next},
        context_instance=RequestContext(request))

class FacebookAuthError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
