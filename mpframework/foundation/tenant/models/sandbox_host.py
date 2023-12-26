#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Represents a URL address the system will accept for a sandbox
"""
from django.db import models
from django.conf import settings

from mpframework.common import constants as mc
from mpframework.common.model import BaseModel
from mpframework.common.model import BaseManager


class SandboxHost( BaseModel ):

    # The sandbox this URL refers to
    sandbox = models.ForeignKey( 'tenant.Sandbox', models.CASCADE, related_name='hosts' )

    # The full server/host url that may be used with this sandbox
    _host_name = models.CharField( unique=True, max_length=mc.CHAR_LEN_UI_LONG,
                db_column='host_name' )

    # Designate URL as the main public face of the sandbox
    main = models.BooleanField( default=False )

    # Designate the main URL if SSL is required
    https = models.BooleanField( default=False )

    # Allow host entries to point to main
    redirect_to_main = models.BooleanField( default=False )

    objects = BaseManager()

    def __str__( self ):
        return self.host_name

    @property
    def host_name( self ):
        """
        HACK DEV - add mpd string to host redirects
        """
        rv = self._host_name
        if settings.DEBUG and settings.MP_CLOUD:
            host_frags = self._host_name.split('.')
            if len( host_frags ) > 2:
                rv = '{}.mpd.{}'.format( host_frags[0], '.'.join( host_frags[1:] ) )
            else:
                rv = 'mpd.{}'.format( '.'.join( host_frags ) )
        return rv
