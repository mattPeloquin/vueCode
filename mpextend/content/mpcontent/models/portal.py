#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PortalItem allows inclusion of content/scripting into portal
    display without protected content.
"""

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager


class PortalItem( BaseItem ):
    """
    Content item that only displays information in the portal,
    i.e., there is no protected content to access.
    """

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Portal item"

    objects = ItemManager()

    def _type_name_PortalItem( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _access_action_PortalItem( self ):
        # DOWNCAST METHOD
        # PortalItems don't have a content action
        return 'action_none'
