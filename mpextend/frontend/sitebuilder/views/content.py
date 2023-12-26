#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder support for content integration
"""
from django.urls import reverse
from django.template.response import TemplateResponse

from mpframework.common.view import staff_required
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import Tree


@staff_required
def content_tree_links( request ):
    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/easylinks/content_links.html', {
                'content': _content_links( request, True ),
                'content_title': "Collection",
                })

@staff_required
def content_item_links( request ):
    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/easylinks/content_links.html', {
                'content': _content_links( request, False ),
                'content_title': "Item",
                })

@staff_required
def content_apis( request ):
    content = []
    for item in BaseItem.objects.active()\
            .filter( request=request ).iterator():
        item_dict = item.dict
        item_dict.update({
                'api_url': reverse( 'api_content_full',
                            kwargs={ 'content_slug': item.slug } ),
                'desc_url': reverse( 'content_description',
                            kwargs={ 'content_slug': item.slug } ),
                'image_url': reverse( 'content_image',
                            kwargs={ 'content_slug': item.slug } ),
                })
        content.append( item_dict )
    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/easylinks/content_apis.html', {
                'content': content,
                })

def _content_links( request, is_tree ):
    if is_tree:
        qs = Tree.objects.active().filter( request=request )
    else:
        qs = BaseItem.objects.active().filter_items( request=request )
    content = []
    for item in qs.iterator():
        item_dict = item.dict
        kwargs = {
            'content_slug': item.node_slug if is_tree else item.slug,
            }
        item_dict.update({
                'site_url': reverse( 'login_content', kwargs=kwargs ),
                'page_url': reverse( 'portal_content', kwargs=kwargs )
                })
        content.append( item_dict )
    return content
