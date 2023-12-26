#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Monkey patch Django Fieldset to prevent it from
    loading default Django media.js files.
"""
from django.forms.widgets import Media
from django.contrib.admin.helpers import Fieldset


@property
def media( self ):
    return Media()

Fieldset.media = media
