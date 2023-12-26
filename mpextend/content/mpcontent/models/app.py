#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Web app proxy
"""

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpextend.content.proxy.models import ProxyModelMixin


class ProxyApp( ProxyModelMixin, BaseItem ):
    """
    Represents the configuration of a paywall proxy to a
    specific web site.
    """

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Web application"

    objects = ItemManager()

    access_type = 'app'

    def _type_name_ProxyApp( self ):
        # DOWNCAST METHOD
        return 'Web app'
