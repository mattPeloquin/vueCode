#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Reusable, customizable themes
"""
from django.db import models
from django.template.defaultfilters import slugify

from mpframework.common import constants as mc
from mpframework.foundation.tenant.models.base import ProviderOptionalModel
from mpframework.foundation.tenant.models import TenantManager

from .template import TemplateCustom
from .theme_mixin import ThemeMixin
from .frame_mixin import FrameSelectMixin


class Theme( ProviderOptionalModel, ThemeMixin, FrameSelectMixin ):
    """
    Captures the ThemeMixin attributes as database items that can be
    referenced by other models.
    Themes define system and user-configurable compositions of UI settings.
    They can be overridden by frame, sandbox, and RequestSkin settings.
    """
    name = models.CharField( db_index=True, max_length = mc.CHAR_LEN_UI_DEFAULT )
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    # Level for access in select boxes
    staff_level = models.IntegerField( choices=TemplateCustom.TEMPLATE_LEVELS,
                blank=True, null=True )

    class Meta:
        verbose_name = u"Theme"

    objects = TenantManager()
    lookup_fields = ( 'name' ,)

    def __str__( self ):
        if self.dev_mode:
            return "f({},p{}){}".format( self.pk, self.provider_optional_id, self.name )
        return self.name

    @property
    def slug_name( self ):
        return slugify( self.name )
