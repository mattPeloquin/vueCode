#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content type groups
"""

from mpframework.common.cache.groups import invalidate_group_provider

from .base.portal import PortalContentMixin
from .base.portal import PortalContentManagerMixin
from . import BaseAttr
from . import ContentManager


class PortalTypeManager( ContentManager, PortalContentManagerMixin ):
    _portalcontent_name = 'type'


class PortalType( BaseAttr, PortalContentMixin ):
    """
    Provider-defined groups that support specialization of content items
    into domain-specific types.

    Type usage is optional; use case would be to specialize different
    groups of Baseitems into conceptual categories.
    Unlike Category, PortalTypes are 1:M relationships used in
    both staff and portal display of content BaseItems.
    Types also send information to the client portal that can be
    associated with content, like adding sb_options.
    """
    class Meta:
        verbose_name = u"Portal type"

    objects = PortalTypeManager()

    sandbox_through_id = 'portaltype_id'

    def invalidate_group( self ):
        """
        Types can be shown in menus, so need to invalidate sandbox
        to refresh staff menu templates.
        """
        super().invalidate_group()
        invalidate_group_provider( self._provider_id )
