#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Associate content with trees
"""
from django.db import models

from mpframework.common.model import BaseModel
from mpframework.foundation.tenant.models.base import TenantManager

from .item import BaseItem


DRAG_ORDER_START = 9999


class TreeBaseItem( BaseModel ):
    """
    MTM table for attaching content to tree nodes
    """
    tree = models.ForeignKey( 'mpcontent.Tree', models.CASCADE,
                related_name='tree_bi_items' )
    item = models.ForeignKey( BaseItem, models.CASCADE,
                related_name='tree_bi_nodes' )

    # What template area should the content be placed in?
    # The lower case names of the areas are used in templates
    AREA = (
        ('A', u"Featured"),
        ('C', u"Core"),
        ('S', u"Support"),
        ('I', u"Custom1"),
        ('J', u"Custom2"),
        ('K', u"Custom3"),
        )
    AREA_DICT = { area[0]: area[1].lower() for area in AREA }
    area = models.CharField( max_length=1, choices=AREA, default='C', blank=False )

    # Ordering used with drag/drop; this is hidden from staff/user
    drag_order = models.IntegerField( default=DRAG_ORDER_START )

    # Is this required to complete the tree?
    # Percentage completion is based on required items
    is_required = models.BooleanField( default=True, verbose_name=u"Required" )

    @staticmethod
    def tenant_arg_filter( _model, sandbox, _provider ):
        """
        TreeBaseItem is not a TenantModel, but uses the TenantManager to allow
        filtering to be overridden for item tenant filtering
        """
        return (), { 'item__sandboxes': sandbox } if sandbox else {}
    objects = TenantManager()

    def __str__( self ):
        if self.dev_mode:
            return "{}-{}(TreeBI{})".format( self.tree.name, self.item.name, self.pk )
        return "{}-{}".format( self.tree.name, self.item.name )

    @property
    def wraps( self ):
        """
        When tree item is asked to represent, assume it is content pointed to.
        """
        return self.item
