#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared content model fields
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.model.fields import mpImageField
from mpframework.common.model.fields import YamlField
from mpframework.common.cache import stash_method_rv


class BaseContentFields( models.Model ):
    """
    Fields defining metadata used with all content models
    """

    # Default UI display (and search) name, which needs to be limited in size
    _name = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_LONG,
                              db_column='name', verbose_name=u"Name" )

    # Text descriptions exposed in the UI
    text1 = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )
    text2 = models.CharField( max_length=mc.CHAR_LEN_UI_BLURB, blank=True )

    # Images for UI display
    image1 = mpImageField( blank=True, null=True )
    image2 = mpImageField( blank=True, null=True )

    # SiteBuilder options
    # Used as blob storage both for MPF options referenced from code and
    # for optional structured data in custom portals.
    # HACK SCALE DB MIGRATE - manually add a FULLTEXT index for DB WHERE
    sb_options = YamlField( null=True, blank=True )

    # Track number of times record has been updated
    revision = models.IntegerField( default=0 )

    # Internal notes for staff -- never displayed to customer
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    class Meta:
        abstract = True

    lookup_fields = ( '_name__icontains', 'id__iexact' ,)

    def __str__( self ):
        if self.dev_mode:
            return "{}({})".format( self.name, self.pk )
        return self.name

    def save( self, *args, **kwargs ):
        """
        Update revision
        """
        self.revision += 1
        super().save( *args, **kwargs )

    @property
    def dict( self ):
        return {
            'id': self.pk,
            'name': self.name,
            'text1': self.text1,
            'text2': self.text2,
            }

    @property
    def name( self ):
        return self._name

    @property
    @stash_method_rv
    def image1_url( self ):
        return self.image1.url if self.image1 else ''
    @property
    @stash_method_rv
    def image2_url( self ):
        return self.image2.url if self.image2 else ''
