#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Display PDF files only in protected viewer
"""

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpframework.content.mpcontent.models.base.files import FileContentMixin


class PDF( FileContentMixin, BaseItem ):
    """
    Upload PDF file that can only be used in special viewer.


    TBD NOW Finish first cut at PDF, with PDF app with
    PDF.js and special byteencoded endpoints
    """

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"PDF"

    objects = ItemManager()

    def _type_name_PDF( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw
