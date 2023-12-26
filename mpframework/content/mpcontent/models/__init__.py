#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content Domain Model

    Content represents what can be sold and provided via
    the mpFramework. Content ownership is tied explicitly
    to providers, and can be shared across sandboxes.
"""

# Convenience imports
from .base.fields import BaseContentFields
from .base.visibility import BaseContentVisibility
from .base.attr import BaseAttr
from .base.manager import ContentManager
from .item_manager import ItemManager
from .item import BaseItem
from .tree import Tree
from .tree_item import TreeBaseItem
from .portal_type import PortalType
from .portal_group import PortalGroup
from .portal_category import PortalCategory
from .file import ProtectedFile

# Lazily create two dicts of MPF content ContentTypes
# One is for filter display, so uses a subset of display model name as key, the other
# is for looking up DB classes so uses the content type model name
from mpframework import mpf_function_group_call
from mpframework import mpf_function_group_register
from django.contrib.contenttypes.models import ContentType

def get_content_item_models():
    if not _content_models:
        for ct in ContentType.objects.filter( app_label='mpcontent' ):
            _content_models[ ct.model ] = ct.model_class()
        from mpframework.common import log
        log.debug("INIT content item models: %s", _content_models)
    return _content_models
_content_models = {}

def get_content_item_types():
    if not _content_types:
        _excludes = mpf_function_group_call('content_non_item_types')
        for ct in ContentType.objects.filter( app_label='mpcontent' ):
            if not [ name for name in _excludes if name in ct.model ]:
                _content_types[ ct.name ] = ct.model_class()
        from mpframework.common import log
        log.debug("INIT content item types: %s", _content_types)
    return _content_types
_content_types = {}

def _non_item_types():
    # Remove DJ model types that aren't actually items
    return [ 'base', 'tree', 'adminproxy',   # Portions of name
                'portalcategory', 'portaltype', 'portalgroup' ]

mpf_function_group_register( 'content_non_item_types', _non_item_types )
