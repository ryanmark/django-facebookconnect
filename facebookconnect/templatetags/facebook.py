# Copyright 2008 Brian Boyer, Ryan Mark, Angela Nitzke, Joshua Pollock,
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
from facebookconnect.models import FacebookTemplate,FacebookProfile

register = template.Library()
    
@register.inclusion_tag('facebook/js.html')
def initialize_facebook_connect():
    return {'facebook_api_key': settings.FACEBOOK_API_KEY}

@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_name(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings,'WIDGET_MODE',None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:name uid="%s" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s">%s</a>' % (p.get_absolute_url(),p.full_name)}

@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_first_name(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings,'WIDGET_MODE',None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:name uid="%s" firstnameonly="true" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s">%s</a>' % (p.get_absolute_url(),p.first_name)}
    
@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_possesive(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'string':u'<fb:name uid="%i" possessive="true" linked="false"></fb:name>' % p.facebook_id}

@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_greeting(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings,'WIDGET_MODE',None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'Hello, <fb:name uid="%s" useyou="false" firstnameonly="true" />' % (p.facebook_id)}
    else:
        return {'string':u'Hello, <a href="%s">%s</a>!' % (p.get_absolute_url(),p.first_name)}

@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_status(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'string':p.status}

@register.inclusion_tag('facebook/show_string.html',takes_context=True)
def show_facebook_photo(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    if getattr(settings,'WIDGET_MODE',None):
        #if we're rendering widgets, link direct to facebook
        return {'string':u'<fb:profile_pic uid="%s" facebook-logo="true" />' % (p.facebook_id)}
    else:
        return {'string':u'<a href="%s"><img src="%s" alt="%s"/></a>' % (p.get_absolute_url(), p.picture_url, p.full_name)}

@register.inclusion_tag('facebook/display.html',takes_context=True)
def show_facebook_info(context,user):
    if isinstance(user,FacebookProfile):
        p = user
    else:
        p = user.facebook_profile
    return {'profile_url':p.get_absolute_url(), 'picture_url':p.picture_url, 'full_name':p.full_name,'networks':p.networks}

@register.inclusion_tag('facebook/mosaic.html')
def show_profile_mosaic(profiles):
    return {'profiles':profiles}

@register.inclusion_tag('facebook/connect_button.html',takes_context=True)
def show_connect_button(context,javascript_friendly=False):
    if 'request' in context:
        req = context['request']
        if req.method == "POST":
            next = req.POST.get('next',req.path)
        else:
            next = req.GET.get('next',req.path)
    else:
        next = ''
    return {'next':next,'javascript_friendly':javascript_friendly}
