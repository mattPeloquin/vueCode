#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Public landing pages

    These pages use MPF template mechanism, but are based on bare templates
    which can optionally inject content or catalog items.
"""
from django.db import models

from mpframework.common.cache import cache_rv
from mpframework.common import constants as mc
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.content.mpcontent.cache import cache_group_content_sandbox
from mpextend.product.catalog.cache import cache_group_catalog


def _cache_group( page ):
    """
    If a landing page is using references to content or catalog items, include
    their group values in the group key.
    """
    rv = page.cache_group
    if page.inject_data:
        if page.inject_data['content']:
            rv += cache_group_content_sandbox( page.sandbox )
        if page.inject_data['catalog']:
            rv += cache_group_catalog( page.sandbox_id )
    return rv


class LandingPage( SandboxModel ):
    """
    Data necessary to display a single public landing page, along with
    support for injecting data into template context
    """

    url = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_DEFAULT )
    title = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT )

    # HTML content/template loaded inside the bare template
    template = models.TextField( blank=True )

    # Inject data into the landing page content, both directly and via references
    # to content and catalog models
    inject_data = YamlField( null=True, blank=True )

    class Meta:
        app_label = 'sitebuilder'
        unique_together = ( 'sandbox', 'url' )

    objects = TenantManager()

    def __str__( self ):
        name = self.title if self.title else self.url
        if self.dev_mode:
            return "cp({},s:{}){}".format( self.pk, self.sandbox_id, name )
        return name

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )

    @cache_rv( keyfn=lambda self:( '', _cache_group( self ) ) )
    def get_context( self ):
        """
        Add context specific to the landing page and support caching it
        """
        rv = {
            'url': self.url,
            'title': self.title,
            }
        if self.inject_data['extra_context']:
            rv.update( self.inject_data['extra_context'] )

        return rv

