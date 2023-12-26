#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Page content view support
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.content.mpcontent.delivery import set_access_response_handler

from ..models import ProtectedPage


def _response_handler( request, access_session ):
    """
    For protected pages, load the page content into the protected page shell
    Links on the page will be handles as separate protected downloads
    """
    log.debug("PROTECTED PAGE response: %s", access_session)

    id = access_session['data']
    page = ProtectedPage.objects.get( _provider_id=request.sandbox._provider_id, id=id )
    return TemplateResponse( request, 'content/page/page.html', {
            'is_page_content': True,
            'content_page': page,
            })

set_access_response_handler( ProtectedPage.access_type, _response_handler )
