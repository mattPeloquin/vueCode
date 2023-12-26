#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content groups for portal display
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.model import CachedModelMixin
from mpframework.content.mpcontent.tags import ContentTagMatchMixin
from mpframework.foundation.tenant.models.base import ProviderOptionalModel
from mpframework.frontend.sitebuilder.models import TemplateCustom

from .base.visibility import BaseContentVisibility
from .base.fields import BaseContentFields
from .base.portal import PortalContentMixin
from .base.portal import PortalContentManagerMixin
from . import ContentManager


class PortalGroupManager( ContentManager, PortalContentManagerMixin ):
    _portalcontent_name = 'group'


class PortalGroup( BaseContentFields, BaseContentVisibility,
            ProviderOptionalModel, CachedModelMixin,
            PortalContentMixin, ContentTagMatchMixin ):
    """
    Unlike other content, Groups are ProviderOptional to support the
    definition of the default groups baked into templates.

    Content is included in groups both through direct selection of a
    PortalGroup in the item/tree AND through tag matching.
    Tag matching used by groups does NOT include parent collections.
    Group tag matching ONLY OCCURS ON THE CLIENT.
    """
    _script_name = models.CharField( db_index=True, blank=True,
                max_length=mc.CHAR_LEN_UI_CODE, db_column='script_name' )

    # Display for trees/items in the group
    nav_template = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )
    item_template = models.ForeignKey( TemplateCustom, models.SET_NULL,
                related_name='+', blank=True, null=True )

    # Optional HTML to display with the group
    html = models.TextField( blank=True )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Portal group"

    objects = PortalGroupManager()

    sandbox_through_id = 'portalgroup_id'

    @property
    def script_name( self ):
        return self._script_name or self.name
