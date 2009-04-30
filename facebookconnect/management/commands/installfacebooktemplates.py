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

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ImproperlyConfigured
from facebook import Facebook
from facebookconnect.models import FacebookTemplate

class Command(BaseCommand):
    def handle(self,*args,**options):
        """Load the templates into facebook (probably clear them out beforehand)"""
        facebook_obj = Facebook(settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)
        
        #blow up all templates
        current_templates = facebook_obj.feed.getRegisteredTemplateBundles()
        for t in current_templates:
            print "Deactivating old bundle #%i ..." % t['template_bundle_id']
            facebook_obj.feed.deactivateTemplateBundleByID(t['template_bundle_id'])
        
        #install templates from our facebook settings file
        for bundle in settings.FACEBOOK_TEMPLATES:
            name = bundle[0]
            one_line_template = bundle[1][0]
            short_template = bundle[1][1]
            full_template = bundle[1][2]
            action_template = bundle[1][3]
            response = facebook_obj.feed.registerTemplateBundle(one_line_template,short_template,full_template,action_template)
            try:
                template = FacebookTemplate.objects.get(name=name)
                #facebook_obj.feed.deactivateTemplateBundleByID(template.template_bundle_id)
                print "Replacing old '%s' bundle ..." % (name.capitalize())
            except FacebookTemplate.DoesNotExist:
                template = FacebookTemplate(name=name)
                print "Loading '%s' bundle ..." % (name.capitalize())
            template.template_bundle_id = response
            template.save()
        
