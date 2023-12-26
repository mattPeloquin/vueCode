#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared MPF code imported across service groups.
    Some is general python code, but many areas make assumptions about
    extending Django or are MPF specific.
"""

from .constants import *

def _( msg ):
    """
    MPF UI string wrapper
    FUTURE - Intended to support translation of strings that won't be moved
    into configuration data.

    FUTURE, PY3 - Holding "" strings over to repace with _("") calls for translation

    """
    return msg
