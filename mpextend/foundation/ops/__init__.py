#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Register as an extension of the MPF ops app
"""

from mpframework.common.app import mpAppConfig


class OpsExtendAppConfig( mpAppConfig ):
    name = 'mpextend.foundation.ops'
    label = 'ops_extend'

    def mp_ready( self ):
        from .events import handle_event_data

default_app_config = 'mpextend.foundation.ops.OpsExtendAppConfig'
