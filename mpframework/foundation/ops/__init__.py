#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    The ops app is a bit of a grab-bag that exists for:

    1) Shared infrastructure, models, and views that cross-cut multiple
       apps or integrate with 3rd party apps which, unlike
       mpframework.common code, require being part of a Django app.

    2) mpFramework management commands. This is instead of splitting
       across other apps, as most commands are cross-cutting.

    3) Misc functionality for operational monitoring and dev needs

    HACK - MPF ASSUMES OPs IS LAST APP LOADED (see below)
"""

from mpframework.common.app import mpAppConfig


class OpsAppConfig( mpAppConfig ):
    name = 'mpframework.foundation.ops'
    label = 'ops'

    def mp_ready( self ):
        """
        HACK - Startup signal
        Normally startup signal is sent as part of uwsgi worker start,
        but for dev and test cases, and lazy apps start, manufacture signal
        based on loading the ops app last.
        """
        from django.conf import settings

        # Register the signal and receiver
        from .receivers import handle_startup

        # Send signal in the dev/test case
        if settings.MP_UWSGI.get('LAZY_APPS') or settings.MP_IS_DJ_SERVER:
            from .signals import startup_signal
            startup_signal.send( sender=self.__class__ )

        # Register Task Bots
        from .bots import WarmBot

default_app_config = 'mpframework.foundation.ops.OpsAppConfig'
