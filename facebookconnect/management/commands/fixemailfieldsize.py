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

class Command(BaseCommand):
    def handle(self,*args,**options):
        """change the database schema to except big email addresses"""
        from django.db import connection, transaction
        cursor = connection.cursor()

        # Data modifying operation - commit required
        cursor.execute("ALTER TABLE `auth_user` CHANGE `email` `email` VARCHAR(255);")
        transaction.commit()
        