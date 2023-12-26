#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ProxyLink content response handlers, which have an initial
    response handler, and follow-on proxy handler.
"""
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from mpframework.common import log
from mpframework.content.mpcontent.delivery import set_access_session
from mpframework.content.mpcontent.delivery import set_access_response_handler
from mpextend.content.proxy.delivery import proxy_access_session

from ..models import ProxyLink


@never_cache
def _response_handler( request, access_session ):
    """
    View provides response for initial iframe link will be loaded into
    and sets up subsequent calls to go to the proxy handler
    """
    log.debug_on() and log.debug("PROTECTED LINK setup response: %s",
                            str(access_session))

    new_session = proxy_access_session( access_session, 'link_proxy' )
    set_access_session( new_session )

    return TemplateResponse( request, 'content/page/iframe_url.html', {
                'is_page_content': True,
                'content_mptype': 'proxylink',
                'content_id': access_session['data'],
                'content_url': access_session['url'],
                })

set_access_response_handler( ProxyLink.access_type, _response_handler )


@never_cache
def _proxy_response_handler( request, access_session ):
    """
    After iframe call makes first call to the proxy, the follow-on
    response will be sent here
    """
    link = ProxyLink.objects.get( _provider_id=request.sandbox._provider_id,
                                    id=access_session['data'] )
    log.debug("PROTECTED LINK proxy response: %s -> %s", link, access_session)
    return link.get_proxy_response( request )

set_access_response_handler( 'link_proxy', _proxy_response_handler )
