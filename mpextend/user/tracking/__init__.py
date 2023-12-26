#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extensions to user functionality
"""

from mpframework.common.app import mpAppConfig

# Imports for mp_async functions loaded by spooler
from . import tracking_update


class TrackingAppConfig( mpAppConfig ):
    name = 'mpextend.user.tracking'
    label = 'tracking'

    def mp_ready( self ):
        from .receivers import handle_user_logged_in

default_app_config = 'mpextend.user.tracking.TrackingAppConfig'
