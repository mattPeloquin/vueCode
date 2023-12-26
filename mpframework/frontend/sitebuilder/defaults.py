#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Values assumed by MPF UI, which can be overridden in options.
"""
from django.conf import settings

from mpframework.common.utils import memoize


UI_DEFAULTS = {
    # Responsive breakpoints used in CSS and JS client code
    'breakpoints': {
        'width_small': settings.MP_SB['BREAKPOINTS']['width_small'],
        'width_medium': settings.MP_SB['BREAKPOINTS']['width_medium'],
        'width_large': settings.MP_SB['BREAKPOINTS']['width_large'],
        'height_small': settings.MP_SB['BREAKPOINTS']['height_small'],
        'height_medium': settings.MP_SB['BREAKPOINTS']['height_medium'],
        },
    }

def _frame_default( frame_type ):
    """
    Factory for method that returns the first system frame of a given
    type for use as a default value.
    """
    from .models import Frame
    filt = {
        'frame_type__in': frame_type,
        'provider_optional_id__isnull': True,
        }
    qs = Frame.objects.filter( **filt )
    if settings.MP_SB['DEFAULT_FRAME']:
        qs = qs.lookup_filter( settings.MP_SB['DEFAULT_FRAME'] )
    rv = qs.first()
    if not rv:
        rv = Frame.objects.filter( **filt ).first()
    return rv

_frame_default_memo = {}
frame_default = memoize( _frame_default, _frame_default_memo )
