#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content categorization groups for user filtering
"""

from .base.attr import BaseAttr
from .base.manager import ContentManager
from .base.portal import PortalContentMixin
from .base.portal import PortalContentManagerMixin


class PortalCategoryManager( ContentManager, PortalContentManagerMixin ):
    _portalcontent_name = 'category'


class PortalCategory( BaseAttr, PortalContentMixin ):
    """
    Provider-defined MTM TreeNode categories used for interactive
    user filtering and potential organizing content in portal UI.
    Categories also send information to the client portal that can be
    associated with content, like adding sb_options.
    """
    class Meta:
        verbose_name = u"Category"
        verbose_name_plural = u"Categories"

    objects = PortalCategoryManager()

    sandbox_through_id = 'portalcategory_id'
