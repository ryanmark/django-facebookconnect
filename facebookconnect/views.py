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
from facebookconnect.models import FacebookProfile

def facebook_login(request):
    if request.method == "POST":
        next = request.POST['next']
        user = authenticate(request=request)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                return HttpResponseRedirect(next)
            else:
                raise FacebookAuthError('This account is disabled.')
        elif request.facebook.uid:
            #we have to set this user up
            return HttpResponseRedirect(reverse('facebook_setup')+"?next=%s" % next)
        else:
            raise FacebookAuthError('Invalid login.')
    else:
        #login_required decorator sent us here
        return render_to_response(
            'accounts/login.html',
            {'hide_primary_login': True,},
            context_instance=RequestContext(request),
        )

def facebook_logout(request):
    logout(request)
    request.facebook.session_key = None
    request.facebook.uid = None
    return HttpResponse('Logged out!')
    #return HttpResponseRedirect('/')
    
def setup(request):
    if not request.facebook.uid:
        return HttpResponseRedirect(reverse('auth_login')+"?next="+request.GET.get('next',''))
    
    if request.method == "POST":
        next = request.POST.get('next','')
        profile = FacebookProfile(facebook_id=request.facebook.uid)
        
        if request.POST.get('facebook_only',False):
            user = User(username=request.facebook.uid, 
                        password=sha.new(str(random.random())).hexdigest()[:8],
                        email=profile.email)
            user.save()
            profile.user = user
            profile.save()
            logging.info("Added user and profile for %s!" % request.facebook.uid)
            user = authenticate(request=request)
            login(request, user)
            return HttpResponseRedirect(next)
            
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            logging.debug("Trying to setup FB: %s, %s" % (user,profile))
            if user is not None and user.is_active:
                profile.user = user
                profile.save()
                logging.info("Attached facebook profile %s to user %s!" % (profile.facebook_id,user))
                login(request, user)
                return HttpResponseRedirect(next)
        else:
            user = User()
            user.facebook_profile = profile
    
    elif request.user.is_authenticated():
        profile = FacebookProfile(facebook_id=request.facebook.uid)
        profile.user = request.user
        profile.save()
        logging.info("Attached facebook profile %s to user %s!" % (profile.facebook_id,user))
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

