#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Proxy base mixin for shared content model behavior
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.cache import stash_method_rv
from mpframework.common.model.fields import YamlField

from .delivery import default_fixups
from .delivery import get_proxy_response


class ProxyModelMixin( models.Model ):
    """
    Shared behavior to configure a content proxy for a web endpoint

    Access to the endpoint is controlled via optional credentials
    passed in the proxy request header.

    FUTURE - simple proxy now, but can evolve into a service with OAuth,
    handling asynchronous jobs that may not be web pages, etc.
    """

    # The main URL for the proxy site
    proxy_main = models.CharField( null=True, blank=True,
                                    max_length=mc.CHAR_LEN_UI_LONG )

    # Add proxy options for credentials, URL mappings, response fixup, etc.
    _proxy_options = YamlField( null=True, blank=True,
                                db_column='proxy_options' )

    class Meta:
        abstract = True

    content_fields = ['proxy_main']

    def save( self, *args, **kwargs ):
        self.update_content_rev()
        super().save( *args, **kwargs )

    @property
    @stash_method_rv
    def proxy_options( self ):
        """
        Lazily update options based on model-specific information
        """
        options = self._proxy_options

        # Setup system defaults for basic cases
        options.setdefault( 'response_text_replace', default_fixups() )

        # Use item tag as default for cache group
        options.setdefault( 'host_cache_id', self.pk )

        return options

    def proxy_url( self, initial=None ):
        """
        Returns URL to call endpoint being proxied, with adjustments
        for context/options
        """
        rv = self.proxy_main

        # If not past the first call, add any starting path
        if initial and self.proxy_options['proxy_start']:
            rv = self.proxy_options['proxy_start']

        return rv

    def get_proxy_response( self, request, session=None ):
        """
        Wrap the general get_proxy_response to support fixups
        driven by model-specific behavior
        """
        first_call_special = session.get('initial') if session else False
        return get_proxy_response( request,
                                   self.proxy_url( first_call_special ),
                                   self.proxy_options )
