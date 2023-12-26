#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Common utilities not dependent in Django apps
"""

from .. import log
from .time_utils import *
from .json_utils import json_dump
from .crypto import get_random_key
from .fn import memoize
from .http import join_urls
from .paths import path_clean
from .paths import join_paths
from .safe_dict import SafeNestedDict
from .user import request_is_authenticated


def safe_int( value ):
    """
    Support converting potential string from unknown source into an
    integer or None - common when converting URL id requests
    """
    try:
        if isinstance( value, str ):
            value = value.strip(' "`\'\n')
        return int( value )
    except Exception as e:
        log.detail3("safe_int fail: %s -> %s", value, e)
        return 0
