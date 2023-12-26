#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code used inside and outside content app
"""

from .search import content_search
from .delivery_utils import *


def content_dict( items ):
    """
    Turn items list into dict of trees and items
    """
    rv = { 'all': [], 'all_ids': [] }
    for item in set( items ):

        rv['all'].append( item )
        rv['all_ids'].append( item.pk )

        group = 'trees' if item.is_collection else 'items'
        rv.setdefault( group, [] ).append( item )

        group = 'tree_ids' if item.is_collection else 'item_ids'
        rv.setdefault( group, [] ).append( item )

    return rv
