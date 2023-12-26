#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Create a dynamic sitemap for each subdomain, focused on top-level collections
    for portal content, and whatever is in the catalog pages.
"""
from django.urls import reverse
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.utils import join_urls
from mpframework.content.mpcontent.models import Tree
from mpframework.content.mpcontent.models import BaseItem


def sandbox_robots( request ):
    return TemplateResponse( request, 'robots.html' )

def sandbox_pwa_manifest( request ):
    return TemplateResponse( request, 'manifest.html',
                content_type='application/json' )

def sandbox_service_worker( request ):
    """
    Load service_worker JS file as endpoint to avoid cross-origin issues.
    """
    return TemplateResponse( request, 'service_worker.html.js',
                content_type='application/javascript' )

def sandbox_sitemap( request ):
    """
    Create list of locations from content collections, catalog, and
    any well-known fixed locations.
    """
    sandbox = request.sandbox
    portal = reverse('portal_view')
    freq = sandbox.options.get( 'sitemap.changefreq', 'weekly' )
    locations = [
        { 'url': portal, 'priority': '1', 'changefreq': freq },
        ]

    # First do addresses for any tree nodes that have explicit slugs defined
    for tree in Tree.objects.mpusing('read_replica')\
                    .filter( sandbox=sandbox, workflow__in='P' )\
                    .exclude( _slug='' )\
                    .iterator():
        locations.append({
            'url': join_urls( portal, tree.slug ),
            'priority': '0.8' if tree.is_top else '0.6',
            'changefreq': freq,
            })

    # Next do any PUBLIC content items with slugs
    for item in BaseItem.objects.mpusing('read_replica')\
                .exclude( _slug='' )\
                .filter_items( sandbox=sandbox, workflow__in='P' )\
                .iterator():
        if( sandbox.options['access.free_public'] or
                item.sb_options['access.free_public'] ):
            locations.append({
                'url': reverse( 'portal_extra',
                            kwargs={ 'ename': 'content', 'evalue': item.slug } ),
                'priority': '0.4',
                'changefreq': freq,
                })

    # Add any explicit links from options
    for item in sandbox.options.get( 'sitemap.extraitems', [] ):
        try:
            locations.append({
                'url': item['url'],
                'priority': item.get( 'priority', '0.4' ),
                'changefreq': item.get( 'changefreq', freq ),
                })
        except Exception:
            log.info("CONFIG - Bad sitemap data: %s -> %s", request.mpipname, item )

    return TemplateResponse( request, 'sitemap.html', context = {
                'site_url': sandbox.main_host_url,
                'locations': locations,
                })
