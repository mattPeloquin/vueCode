#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Webhooks for MPF events
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager


class WebHook( SandboxModel ):
    """
    The WebHook model defines a set of events that will call external URLs

    These are called from other code as needed to indicate the event.
    """

    # Events that will be sent are defined here
    WEBHOOK_EVENTS = (
        ('user_joined', u"User joined"),
        ('content_started', u"Content started"),
        ('content_completed', u"Content completed"),
        )
    hook_event = models.CharField( max_length=32, blank=True, choices=WEBHOOK_EVENTS )

    name = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT )
    url = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Define how a webhook sends data
    WEBHOOK_DATA = (
        ('QS', u"Querystring"),
        ('HD', u"Request header"),
        )
    hook_data = models.CharField( max_length=2, blank=False,
                                    choices=WEBHOOK_DATA, default='QS' )

    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        app_label = 'sitebuilder'

    objects = TenantManager()

    def __str__( self ):
        if self.dev_mode:
            return "pf({},s:{}){}".format( self.pk, self.sandbox_id, self.name )
        return self.name
