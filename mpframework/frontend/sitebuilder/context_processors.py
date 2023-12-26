#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder context primarily drives per-request changes to templates.
"""
from django.conf import settings
from django.urls import reverse

from mpframework.common.utils.request import lazyrequest
from mpframework.common.cache.template import template_cache_sandbox
from mpframework.common.cache.template import template_cache_page
from mpframework.common.cache.template import template_cache_auth
from mpframework.common.cache.template import template_cache_staff
from mpframework.content.mpcontent.models import Tree
from mpframework.content.mpcontent.models import BaseItem

from .models import TemplateCustom
from .utils import get_themes
from .utils import get_frames
from .utils import get_templates


NUM_CONTENT_LINKS = 3


def portal( request ):
    if request.is_lite or request.is_api:
        return {}

    # Prevent template caching here by setting timeout; this is
    # not great, but convenient place since Django doesn't have
    # a hook - alternative is a custom cache tag
    if( getattr( request, 'mp_template_no_cache', False ) or
        getattr( request, 'mp_template_no_page_cache', False ) ):
        ttime = 0
    else:
        ttime = settings.MP_CACHE_AGE['TEMPLATE']

    return {
        'request_skin': request.skin,
        'sb_options': request.skin.sb_options,

        # Timeout for template caching
        'ttime': ttime,

        # Lazy calls for HTML page fragment keys
        # Delay call of template keys unless needed, and then stash in request
        'template_cache_sandbox': lazyrequest( template_cache_sandbox, request ),
        'template_cache_page': lazyrequest( template_cache_page, request ),
        'template_cache_auth': lazyrequest( template_cache_auth, request ),
        'template_cache_staff': lazyrequest( template_cache_staff, request ),

        # Client script templates for insertion
        'platform_templates': lazyrequest( _platform_templates, request ),
        'portal_templates': lazyrequest( _portal_templates, request ),

        # Content-specific portal?
        'request_content': _request_content( request ),

        # Sitebuilder displays in tools and staff menus
        'sb_portal': reverse('easy_portal'),
        'sb_themes': lazyrequest( get_themes, request ),
        'sb_vueportals': lazyrequest( get_frames, request, 'P' ),
        'sb_vuetrees': lazyrequest( get_frames, request, 'C' ),
        'sb_vueitems': lazyrequest( get_frames, request, 'I' ),
        'sb_styles': lazyrequest( get_templates, request, 'B' ),

        # Pick up the most recently edited items for use with content links
        'sb_sample_tops': lazyrequest( _tops, request, NUM_CONTENT_LINKS ),
        'sb_sample_items': lazyrequest( _items, request, NUM_CONTENT_LINKS ),
        }

def _platform_templates( request ):
    tm = TemplateCustom.objects
    return tm.template_list( request.sandbox, tm.model.PLATFORM_TEMPLATES )
def _portal_templates( request ):
    tm = TemplateCustom.objects
    return tm.template_list( request.sandbox, tm.model.PORTAL_TEMPLATES )

def _request_content( request ):
    content = request.mpstash.get('request_content')
    return content.pk if content else False

def _tops( request, limit ):
    return list( Tree.objects.filter_tops( request=request )
                    .order_by('-hist_modified')[:limit] )
def _items( request, limit ):
    return list( BaseItem.objects.filter_items( request=request )
                    .order_by('-hist_modified')[:limit] )
