#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ProxyApp content response handlers, which have an initial
    response handler, and follow-on proxy handler
"""
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from mpframework.common import log
from mpframework.content.mpcontent.delivery import set_access_session
from mpframework.content.mpcontent.delivery import set_access_response_handler
from mpextend.content.proxy.delivery import proxy_access_session

from ..models import ProxyApp


@never_cache
def _response_handler( request, access_session ):
    """
    Displays the page with iframe the proxy site will be loaded into
    and sets up subsequent calls to go to the proxy handler.
    """
    log.debug("PROTECTED APP SETUP: %s", access_session)

    new_session = proxy_access_session( access_session, 'app_proxy' )
    set_access_session( new_session )

    return TemplateResponse( request, 'content/page/iframe_url.html', {
            'is_page_content': True,
            'content_mptype': 'proxyapp',
            'content_id': new_session['data'],
            'content_url': new_session['url'],
            })

set_access_response_handler( ProxyApp.access_type, _response_handler )


def _proxy_response_handler( request, access_session ):
    """
    All calls to the proxy source go through here.
    Requests are made to the protected content access url with any additional
    URL to be passed on to the proxy source.
    """
    id = access_session['data']
    app = ProxyApp.objects.get( _provider_id=request.sandbox._provider_id, id=id )
    log.debug_on() and log.debug("PROTECTED APP PROXY: %s -> %s",
                            app, str(access_session))

    # Make the call to source server, and fixup the response
    rv = app.get_proxy_response( request, access_session )

    # If this is first time through, mark proxy session as initialized
    # This should not have issues with race conditions, as the first call here is
    # in response to access call from template proxy, of which there should
    # only be one per session.
    if access_session['initial']:
        access_session['initial'] = False
        set_access_session( access_session )

    return rv

set_access_response_handler( 'app_proxy', _proxy_response_handler )
