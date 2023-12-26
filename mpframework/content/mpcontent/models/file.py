#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Protected files that can be downloaded or played
"""

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpframework.content.mpcontent.models.base.files import FileContentMixin

# TBD DB - file mixin

class ProtectedFile( FileContentMixin, BaseItem ):
    """
    Wraps files that can be directly downloaded

    FUTURE - size of document, autodetect?
    """

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Download"

    objects = ItemManager()

    def _type_name_ProtectedFile( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _access_action_ProtectedFile( self ):
        """
        Default file action should be download
        DOWNCAST METHOD
        """
        return self._action if self._action else 'action_download'
