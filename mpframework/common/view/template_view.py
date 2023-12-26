#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extend Django's TemplateView
"""
from django.views.generic import TemplateView


class mpTemplateView( TemplateView ):
    """
    Support passing context flags
    """

    extra_context = {}

    def get_context_data( self, **kwargs ):
        rv = super().get_context_data( **kwargs )
        rv.update( self.extra_context )
        return rv
