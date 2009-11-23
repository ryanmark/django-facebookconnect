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

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.contrib.auth import REDIRECT_FIELD_NAME

from facebook.djangofb import get_facebook_client
from facebookconnect.models import FacebookTemplate, FacebookProfile

register = template.Library()
    
@register.inclusion_tag('facebook/js.html')
def initialize_facebook_connect():
    return {'facebook_api_key': settings.FACEBOOK_API_KEY}

@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_name(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings, 'WIDGET_MODE', None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:name uid="%s" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s">%s</a>' % (p.get_absolute_url(), p.full_name)}

@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_first_name(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings, 'WIDGET_MODE', None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:name uid="%s" firstnameonly="true" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s">%s</a>' % (p.get_absolute_url(), p.first_name)}
    
@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_possesive(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'string':u'<fb:name uid="%i" possessive="true" linked="false"></fb:name>' % p.facebook_id}

@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_greeting(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings, 'WIDGET_MODE', None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'Hello, <fb:name uid="%s" useyou="false" firstnameonly="true" />' % (p.facebook_id)}
    else:
        return {'string':u'Hello, <a href="%s">%s</a>!' % (p.get_absolute_url(), p.first_name)}

@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_status(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'string':p.status}

@register.inclusion_tag('facebook/show_string.html', takes_context=True)
def show_facebook_photo(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if p.get_absolute_url(): url = p.get_absolute_url()
    else: url = ""
    if p.picture_url: pic_url = p.picture_url
    else: pic_url = ""
    if p.full_name: name = p.full_name
    else: name = ""
    if getattr(settings, 'WIDGET_MODE', None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:profile_pic uid="%s" facebook-logo="true" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s"><img src="%s" alt="%s"/></a>' % (url, pic_url, name)}

@register.inclusion_tag('facebook/display.html', takes_context=True)
def show_facebook_info(context, user):
    if isinstance(user, FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'profile_url':p.get_absolute_url(), 'picture_url':p.picture_url, 'full_name':p.full_name, 'networks':p.networks}

@register.inclusion_tag('facebook/mosaic.html')
def show_profile_mosaic(profiles):
    return {'profiles':profiles}

@register.inclusion_tag('facebook/connect_button.html', takes_context=True)
def show_connect_button(context):
    if REDIRECT_FIELD_NAME in context:
        redirect_url = context[REDIRECT_FIELD_NAME]
    else: redirect_url = False
    
    if ('user' in context and hasattr(context['user'], 'facebook_profile') and
         context['user'].facebook_profile and
         context['user'].facebook_profile.is_authenticated()):
        logged_in = True
    else: logged_in = False
    return {REDIRECT_FIELD_NAME:redirect_url, 'logged_in':logged_in}

@register.simple_tag
def facebook_js():
    return '<script src="http://static.ak.connect.facebook.com/js/api_lib/v0.4/FeatureLoader.js.php" type="text/javascript"></script>'

@register.simple_tag
def show_logout():
    o = reverse('facebook_logout')
    return '<a href="%s" onclick="FB.Connect.logoutAndRedirect(\'%s\');return false;">logout</a>' % (o, o) #hoot!

@register.filter()
def js_string(value):
    import re
    return re.sub(r'[\r\n]+', '', value)

@register.inclusion_tag('facebook/invite.html')
def show_invite_link(invitation_template="facebook/invitation.fbml", show_link=True):
    """display an invite friends link"""
    fb = get_facebook_client()
    current_site = Site.objects.get_current()
    
    content = render_to_string(invitation_template,
                               { 'inviter': fb.uid,
                                 'url': fb.get_add_url(),
                                 'site': current_site })
    
    from cgi import escape 
    content = escape(content, True) 

    facebook_uid = fb.uid
    fql = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1='%s') AND has_added_app = 1" % fb.uid
    result = fb.fql.query(fql)
    # Extract the user ID's returned in the FQL request into a new array.
    if result and isinstance(result, list):
        friends_list = map(lambda x: str(x['uid']), result)
    else: friends_list = []
    # Convert the array of friends into a comma-delimeted string.
    exclude_ids = ','.join(friends_list) 
    
    return {
        'exclude_ids':exclude_ids,
        'content':content,
        'action_url':'',
        'site':current_site,
        'show_link':show_link,
    }