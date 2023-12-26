#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code shared between Sandbox and Theme for setting frames

    Each sandbox portal/link endpoint needs a frame, which may
    be defined at the theme, sandbox, and system default levels.
"""
from django.db import models


class FrameSelectMixin( models.Model ):
    """
    Default sandbox portal endpoint Frames for site, collection, and items.
    Nulls indicate using the default, which is ultimately set by system.
    """

    frame_site = models.ForeignKey( 'sitebuilder.Frame',
                                    models.SET_NULL, blank=True, null=True,
                                    related_name='+' )
    frame_tree = models.ForeignKey( 'sitebuilder.Frame',
                                    models.SET_NULL, blank=True, null=True,
                                    related_name='+' )
    frame_item = models.ForeignKey( 'sitebuilder.Frame',
                                    models.SET_NULL, blank=True, null=True,
                                    related_name='+' )
    class Meta:
        abstract = True

    def frame_for_type( self, frame_type ):
        """
        Mechanism to get frame default based on type
        """
        return getattr( self, self._frame_types.get( frame_type ), None )

    _frame_types = {
        'P': 'frame_site',
        'C': 'frame_tree',
        'I': 'frame_item',
        }
