#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for portal-specific content
"""
from django.db import models

from mpframework.common.cache import cache_rv
from ...cache import cache_keyfn_content


class PortalContentManagerMixin:
    """
    Cache item types for this sandbox's configuration
    """

    def _portalcontent_keyfn( self, request ):
        key, group = cache_keyfn_content( request )
        key = self._portalcontent_name + key
        return key, group

    @cache_rv( keyfn=_portalcontent_keyfn )
    def get_portal_objs( self, request ):
        return self._get_portal_objs( request=request )

    @cache_rv( keyfn=_portalcontent_keyfn )
    def get_tree_objs( self, request ):
        return self._get_portal_objs( request=request, scope__in='BC' )

    @cache_rv( keyfn=_portalcontent_keyfn )
    def get_item_objs( self, request ):
        return self._get_portal_objs( request=request, scope__in='BI' )

    def _get_portal_objs( self, **kwargs ):
        return list( self.mpusing('read_replica')\
                        .filter( **kwargs )\
                        .iterator() )


class PortalContentMixin( models.Model ):
    """
    Behavior shared across portal groupings
    """

    # How should items in the collection be displayed in the portal
    PORTAL_SCOPE = (
        ('B', u"Collections and items"),
        ('C', u"Collections only"),
        ('I', u"Items only"),
        )
    scope = models.CharField( max_length=1, choices=PORTAL_SCOPE,
                              default='B' )
    class Meta:
        abstract = True
