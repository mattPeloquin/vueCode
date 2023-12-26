#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Quiz view support
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.content.mpcontent.delivery import set_access_response_handler

from ..models import Quiz


def _response_handler( request, access_session ):
    """
    Raw pages are similar to pages, but don't frame the HTML content
    """
    log.debug("PROTECTED QUIZ response: %s", access_session)

    id = access_session['data']
    item = Quiz.objects.get_quiet( _provider_id=request.sandbox._provider_id, id=id )
    return TemplateResponse( request, 'content/page/quiz.html', {
            'is_page_content': True,
            'quiz': item,
            })

set_access_response_handler( Quiz.access_type, _response_handler )
