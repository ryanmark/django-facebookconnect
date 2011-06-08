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
log = logging.getLogger('facebookconnect.views')

from datetime import datetime
import hashlib,pdb
import urllib
import time
import urllib2
import urlparse
import facebook

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings

from facebookconnect.models import FacebookProfile
from facebookconnect.forms import FacebookUserCreationForm

cookie_key = 'fbs_' + settings.FACEBOOK_APP_ID
cookie_path = '/'
cookie_domain = settings.SESSION_COOKIE_DOMAIN

def facebook_login(request, redirect_url=None,
                   template_name='facebook/login.html',
                   extra_context=None):
    """
    facebook_login
    ===============================
    
    Handles logging in a facebook user. Usually handles the django side of
    what happens when you click the facebook connect button. The user will get
    redirected to the 'setup' view if thier facebook account is not on file.
    If the user is on file, they will get redirected. You can specify the
    redirect url in the following order of presidence:
    
     1. whatever url is in the 'next' get parameter passed to the facebook_login url
     2. whatever url is passed to the facebook_login view when the url is defined
     3. whatever url is defined in the LOGIN_REDIRECT_URL setting directive
    
    Sending a user here without login will display a login template.
    
    If you define a url to use this view, you can pass the following parameters:
     * redirect_url: defines where to send the user after they are logged in. This
                     can get overridden by the url in the 'next' get param passed on 
                     the url.
     * template_name: Template to use if a user arrives at this page without submitting
                      to it. Uses 'facebook/login.html' by default.
     * extra_context: A context object whose contents will be passed to the template.
    """
    # User is logging in
    if request.method == "POST":
        log.debug("OK logging in...")
        url = reverse('facebook_setup')
        if request.POST.get(REDIRECT_FIELD_NAME,False):
            url += "?%s=%s" % (REDIRECT_FIELD_NAME, request.POST[REDIRECT_FIELD_NAME])
        elif redirect_url:
            url += "?%s=%s" % (REDIRECT_FIELD_NAME, redirect_url)
        user = authenticate(request=request)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                log.debug("Redirecting to %s" % url)
                return HttpResponseRedirect(url)
            else:
                log.debug("This account is disabled.")
                raise FacebookAuthError('This account is disabled.')
        elif request.facebook.uid:
            #we have to set this user up
            log.debug("Redirecting to setup")
            return HttpResponseRedirect(url)
    
    # User is already logged in
    elif request.user.is_authenticated:
        if request.REQUEST.get(REDIRECT_FIELD_NAME,False):
            redirect_url = request.REQUEST[REDIRECT_FIELD_NAME]
        elif redirect_url is None:
            redirect_url = getattr(settings, "LOGIN_REDIRECT_URL", "/")
        
        HttpResponseRedirect(redirect_url)

    # User ain't logged in
    # here we handle extra_context like it is done in django-registration
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    template_dict = {}
    # we only need to set next if its been passed in the querystring or post vars
    if request.REQUEST.get(REDIRECT_FIELD_NAME, False):
        template_dict.update({REDIRECT_FIELD_NAME:request.REQUEST[REDIRECT_FIELD_NAME]})

    return render_to_response(
        template_name,
        template_dict,
        context_instance=context)
    
    
def facebook_logout(request, redirect_url=None):
    """
    facebook_logout
    ============================
    
    Logs the user out of facebook and django.
    
    If you define a url to use this view, you can pass the following
    parameters:
     * redirect_url: defines where to send the user after they are logged out.
                     If no url is pass, it defaults to using the 
                     'LOGOUT_REDIRECT_URL' setting.
    
    """
    logout(request)
    if getattr(request,'facebook',False):
        request.facebook.session_key = None
        request.facebook.uid = None
    url = getattr(settings,'LOGOUT_REDIRECT_URL',redirect_url) or '/'
    return HttpResponseRedirect(url)
    
def setup(request,redirect_url=None,
          registration_form_class=FacebookUserCreationForm,
          template_name='facebook/setup.html',
          extra_context=None):
    """
    setup
    ===============================
    
    Handles a new facebook user. There are three ways to setup a new facebook user.
     1. Link the facebook account with an existing django account.
     2. Create a dummy django account to attach to facebook. The user must always use
        facebook to login.
     3. Ask the user to create a new django account
     
    The built in template presents the user with all three options. Once setup is 
    complete the user will get redirected. The url used in the following order of 
    presidence:

      1. whatever url is in the 'next' get parameter passed to the setup url
      2. whatever url is passed to the setup view when the url is defined
      3. whatever url is defined in the LOGIN_REDIRECT_URL setting directive
    
    If you define a url to use this view, you can pass the following parameters:
     * redirect_url: Defines where to send the user after they are setup. This
                     can get overridden by the url in the 'next' get param passed on 
                     the url.
     * registration_form_class: Django form class to use for new user way #3 explained
                                above. The form should create a new user.
     * template_name: Template to use. Uses 'facebook/setup.html' by default.
     * extra_context: A context object whose contents will be passed to the template.
    """
    log.debug('in setup view')
    #you need to be logged into facebook.
    if not request.facebook.uid:
        log.debug('Need to be logged into facebook')
        url = reverse(facebook_login)
        if request.REQUEST.get(REDIRECT_FIELD_NAME,False):
            url += "?%s=%s" % (REDIRECT_FIELD_NAME, request.REQUEST[REDIRECT_FIELD_NAME])
        return HttpResponseRedirect(url)

    #setup forms
    login_form = AuthenticationForm()
    registration_form = registration_form_class()

    #figure out where to go after setup
    if request.REQUEST.get(REDIRECT_FIELD_NAME,False):
        redirect_url = request.REQUEST[REDIRECT_FIELD_NAME]
    elif redirect_url is None:
        redirect_url = getattr(settings, "LOGIN_REDIRECT_URL", "/")

    #check that this fb user is not already in the system
    try:
        FacebookProfile.objects.get(facebook_id=request.facebook.uid)
        # already setup, move along please
        return HttpResponseRedirect(redirect_url)
    except FacebookProfile.DoesNotExist, e:
        # not in the db, ok to continue
        pass

    #user submitted a form - which one?
    if request.method == "POST":
        log.debug('Submitted form')
        #lets setup a facebook only account. The user will have to use
        #facebook to login.
        if request.POST.get('facebook_only',False):
            log.debug('Facebook Only')
            profile = FacebookProfile(facebook_id=request.facebook.uid)
            user = User(username=request.facebook.uid,
                        email=profile.email)
            user.set_unusable_password()
            user.save()
            profile.user = user
            profile.save()
            log.info("Added user and profile for %s!" % request.facebook.uid)
            user = authenticate(request=request)
            login(request, user)
            return HttpResponseRedirect(redirect_url)
        
        # user setup his/her own local account in addition to their facebook
        # account. The user will have to login with facebook unless they 
        # reset their password.
        elif request.POST.get('register',False):
            log.debug('Register a new account')
            profile = FacebookProfile(facebook_id=request.facebook.uid)
            if profile.first_name != "(Private)":
                fname = profile.first_name
            if profile.last_name != "(Private)":
                lname = profile.last_name
            user = User(first_name=fname, last_name=lname)
            registration_form = registration_form_class(
                                        data=request.POST, instance=user)
            if registration_form.is_valid():
                user = registration_form.save()
                profile.user = user
                profile.save()
                log.info("Added user and profile for %s!" % request.facebook.uid)
                login(request, authenticate(request=request))
                return HttpResponseRedirect(redirect_url)
            else:
                request.user = User()
                request.user.facebook_profile = FacebookProfile(facebook_id=request.facebook.uid)
    
        #user logs in in with an existing account, and the two are linked.
        elif request.POST.get('login',False):
            login_form = AuthenticationForm(data=request.POST)

            if login_form.is_valid():
                user = login_form.get_user()
                log.debug("Trying to setup FB: %s, %s" % (user,request.facebook.uid))
                if user and user.is_active:
                    FacebookProfile.objects.get_or_create(user=user, facebook_id=request.facebook.uid)
                    log.info("Attached facebook profile %s to user %s!" % (request.facebook.uid, user))
                    login(request, user)
                    return HttpResponseRedirect(redirect_url)
            else:
                request.user = User()
                request.user.facebook_profile = FacebookProfile(facebook_id=request.facebook.uid)
    
    #user didn't submit a form, but is logged in already. We'll just link up their facebook
    #account automatically.
    elif request.user.is_authenticated():
        log.debug('Already logged in')
        try:
            request.user.facebook_profile
        except FacebookProfile.DoesNotExist:
            profile = FacebookProfile(facebook_id=request.facebook.uid)
            profile.user = request.user
            profile.save()
            log.info("Attached facebook profile %s to user %s!" % (profile.facebook_id,profile.user))

        return HttpResponseRedirect(redirect_url)
    
    # user just showed up
    else:
        log.debug('Setting up form...')
        request.user.facebook_profile = profile = FacebookProfile(facebook_id=request.facebook.uid)
        login_form = AuthenticationForm(request)
        log.debug('creating a dummy user')
        fname = lname = ''
        if profile.first_name != "(Private)":
            fname = profile.first_name
        if profile.last_name != "(Private)":
            lname = profile.last_name
        user = User(first_name=fname, last_name=lname)
        registration_form = registration_form_class(instance=user)
    
    log.debug('going all the way...')
    
    # add the extra_context to this one
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    template_dict = {
        "login_form":login_form,
        "registration_form":registration_form
    }
    
    # we only need to set next if its been passed in the querystring or post vars
    if request.REQUEST.get(REDIRECT_FIELD_NAME, False):
        template_dict.update( {REDIRECT_FIELD_NAME: request.REQUEST[REDIRECT_FIELD_NAME]})
        
    return render_to_response(
        template_name,
        template_dict,
        context_instance=context)

class FacebookAuthError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

# From https://github.com/SeanHayes/django-facebook-oauth

def fb_auth(request):
    v_code = request.GET.get('code')
    APP_ID = settings.FACEBOOK_APP_ID
    FB_P=settings.FB_PERM
    next = request.GET['next'] if 'next' in request.GET else settings.FB_AUTH_REDIRECT if hasattr(settings, "FB_AUTH_REDIRECT") else '/'

    if cookie_key in request.COOKIES:
        log.debug('cookie value: %s' % request.COOKIES[cookie_key])
        user = authenticate(cookies=request.COOKIES)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(next)
        else:
            log.debug("no user was returned")

    if(v_code):
        log.debug('v_code: %s' % v_code)
        user = authenticate(verification_code=v_code)
        if user is not None:
            log.debug(user)
            if user.is_active:
                log.debug('logging in...')
                login(request, user)
                resp=HttpResponseRedirect(next)
                access_token = user.facebook_profile.access_token

                #if request.META.has_key('HTTP_REFERER'):
                #	url = request.META['HTTP_REFERER']
                #	resp=HttpResponseRedirect(urllib2.unquote(url))
                #else:
                #	resp=HttpResponseRedirect("http://"+settings.SESSION_COOKIE_DOMAIN)

                resp=HttpResponseRedirect(next)

                if(FB_P.count('offline_access')):
                    resp=set_cookie(resp, "fbs_"+APP_ID, user.username, access_token=access_token, expires=time.time() + 30 * 86400)
                else:
                    resp=set_cookie(resp, "fbs_"+APP_ID, user.username, access_token=access_token, expires=time.time() + 3600)
                return resp
            else:
                # user is deactivated
                pass
        else:
            #authentication failed
            pass

    else:
        #log.debug('last case')
        url = 'http://%s%s' % (settings.HOST, reverse('fb_auth'))
        log.debug(url)
        perm=",".join(FB_P)
        args = dict(client_id=APP_ID, redirect_uri=url, scope=perm)
        resp = HttpResponseRedirect("https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(args))
        #it's possible the cookie could be stale
        resp.delete_cookie(cookie_key, cookie_path, cookie_domain)
        return resp

def set_cookie(resp, name, value, access_token=None, domain=None, path="/", expires=None):
    """Generates and signs a cookie for the give name/value"""
    expires = str(int(time.time())+21600000)
    args = {}
    args['expires'] = expires
    args['uid'] = value
    if(access_token):
        args['access_token'] = access_token
        graph = facebook.GraphAPI(access_token)
        graph=graph.get_object('me')
        fname = graph['first_name']
        args['fname']=fname

    for arg in args:
        if type(args[arg]) is unicode:
            args[arg] = args[arg].encode('utf-8')
    signature = cookie_signature(args)
    args['sig'] = signature

    #resp.set_cookie(name,urllib.urlencode(args),path="/",domain=cookie_domain,expires=str(int(time.time())+21600000))
    max_age = 365*24*60*60
    resp.set_cookie(name,urllib.urlencode(args), max_age=max_age, expires=None, path=cookie_path, domain=cookie_domain, secure=None)
    return resp

def cookie_signature(parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    payload = []
    for part in sorted(parts.keys()):
        payload.append('%s=%s' % (part, parts[part]))
    payload.append(settings.FACEBOOK_SECRET_KEY)
    payload = ''.join(payload)

    return hashlib.md5(payload).hexdigest()


