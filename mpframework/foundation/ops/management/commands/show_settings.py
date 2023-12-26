#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Show the settings values
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from mpframework.common import log

class Command( BaseCommand ):
    args = ''
    help = 'Show settings'

    # The DB may not be created or accessible
    requires_model_validation = False

    def handle(self, *args, **options):
        setting_dict = {}
        for name in sorted( settings.__dir__() ):
            if not name.startswith('__'):
                setting_dict[ name ] = eval('settings.' + name)

        for name, value in setting_dict.items():
            log.info("%s: %s", name, value)
