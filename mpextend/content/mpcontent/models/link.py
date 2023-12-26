#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Proxy external links as content items
"""
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.cache import stash_method_rv
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager

from mpextend.content.proxy.models import ProxyModelMixin


class ProxyLink( ProxyModelMixin, BaseItem ):
    """
    Supports a proxy for protecting shared links

    Used with private links to content on another site, accessed through
    a proxy with configurable fixup.
    Also supports links to shares that are publically accessible, to allow
    incorporation of content from sites that are difficult/impossible to proxy.
    """

    # Configuration for different external link platforms
    LINK_TYPES = tuple( ( k, v['name'] ) for k, v in
                        sorted( settings.MP_CONTENT['LINK_TYPES'].items() ) )
    link_type = models.CharField( max_length=16, choices=LINK_TYPES,
                                  default=LINK_TYPES[0], blank=False )

    # Simple credentials for use with some link types
    username = models.CharField( max_length=mc.CHAR_LEN_UI_CODE, blank=True )
    password = models.CharField( max_length=mc.CHAR_LEN_UI_CODE, blank=True )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Protected link"

    objects = ItemManager()

    access_type = 'link'

    def _type_name_ProxyLink( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _access_action_ProxyLink( self ):
        """
        Change default action to be inline, to match with the default of
        public direct links to content (much of which won't run in iframe).
        DOWNCAST METHOD
        """
        return self._action if self._action else 'action_inline'

    @property
    def link_config( self ):
        """
        Return the configuration dict for the selected type
        """
        try:
            return settings.MP_CONTENT['LINK_TYPES'][ self.link_type ]
        except Exception:
            log.exception("Link type not in configuration: %s", self.link_type)
            return {}

    @property
    @stash_method_rv
    def proxy_options( self ):
        """
        Return options for the type combined with any additional options
        """
        rv = self.link_config.get( 'proxy_options', {} )
        rv.update( super().proxy_options )
        return rv

    def get_access_url( self, request, **kwargs ):
        """
        Support special case of direct proxy links
        """
        if self.link_config.get('direct'):
            log.info2('LINK direct: %s -> %s', request.mpipname, self.proxy_main)
            return self.proxy_main

        return super().get_access_url( request, **kwargs )
