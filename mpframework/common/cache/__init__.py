#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Wrap Django cache support to provide for easily managing
    invalidation groups, multiple caches, and caching
    return values from functions and models.
"""

# Convenance imports for the most common common items
from .rv import cache_rv
from .version import cache_version
from .clear import invalidate_key
from .clear import invalidate_cache_group
from .stash import stash_method_rv
from .stash import clear_stashed_methods
