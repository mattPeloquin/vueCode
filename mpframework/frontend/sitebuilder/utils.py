#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder general shared code
"""

from mpframework.common.cache import cache_rv
from mpframework.foundation.tenant.query_filter import provider_optional_name_filter_fk

from .models import Theme
from .models import Frame
from .models import TemplateCustom


@cache_rv( cache='template', keyfn=lambda r:(
            r.user.staff_level, r.sandbox.provider.cache_group ))
def get_themes( request ):
    """
    Return and cache list of themes for select box with overridden system
    themes removed.
    """
    qs = Theme.objects.filter(
            TemplateCustom.has_access_Q( request.user.staff_level ),
            provider_optional_system=request.sandbox.provider )
    return list( provider_optional_name_filter_fk( qs ) )

@cache_rv( cache='template', keyfn=lambda r, t:(
            str(r.user.staff_level) + str(t),
            r.sandbox.provider.cache_group ))
def get_frames( request, types ):
    if request.user.has_test_access:
        types += 'K'
    return list( Frame.objects.filter(
            Frame.has_access_Q( request.user.staff_level ),
            _provider=request.sandbox.provider,
            frame_type__in=types ))

@cache_rv( cache='template', keyfn=lambda r, t:(
            str(r.user.staff_level) + str(t),
            r.sandbox.provider.cache_group ))
def get_templates( request, type ):
    """
    Return and cache templates of a given type
    """
    qs = TemplateCustom.objects.filter(
            TemplateCustom.has_access_Q( request.user.staff_level ),
            template_type=type,
            provider_optional_system=request.sandbox.provider )
    return list( provider_optional_name_filter_fk( qs ) )
