#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Application to support the LMS content type
"""

from mpframework.common.app import mpAppConfig


class LmsAppConfig( mpAppConfig ):
    name = 'mpextend.content.lms'
    label = 'lms'

    def mp_ready( self ):
        from .receivers import handle_startup

default_app_config = 'mpextend.content.lms.LmsAppConfig'
