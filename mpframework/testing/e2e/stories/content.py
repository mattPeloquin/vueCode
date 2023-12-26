#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    EasyVue product creation and modification of items tied to products
"""

from random import randint

from ..blocks import ContentBlock
from ..blocks import CollectionsBlock


def new_content( stc, number, **kwargs ):
    """
    Returns list with the given number of ContentBlocks, with
    optional verification that product was created
    """
    rv = []
    verify = kwargs.pop( 'verify', False )

    for count in range( 0, number ):
        cb = ContentBlock( stc, **kwargs )
        if verify:
            cb.verify_portal()
            cb.verify_admin()
        rv.append( cb )

    return rv

def new_collection( stc, number, **kwargs ):
    """
    Returns list with the given number of ContentBlocks, with
    optional verification that product was created
    """
    rv = []
    verify = kwargs.pop( 'verify', False )

    for count in range( 0, number ):
        cb = CollectionsBlock( stc, **kwargs )
        if verify:
            cb.verify_portal()
            cb.verify_admin()
        rv.append( cb )

    return rv

def new_content_and_collections( stc, number, **kwargs ):
    """
    Returns list with the given number of ContentBlocks, with
    optional verification that product was created
    """
    rv = []
    verify = kwargs.pop( 'verify', False )

    for count in range( 0, number ):
        if randint(0, 10) < 5:
            cb = CollectionsBlock( stc, **kwargs )
        else:
            cb = ContentBlock( stc, **kwargs )

        if verify:
            cb.verify_portal()
            cb.verify_admin()
        rv.append( cb )

    return rv
