#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content Embed view support
"""
from django.template.response import TemplateResponse
from django.template.context import make_context

from mpframework.common import log
from mpframework.common.template import mpTemplate
from mpframework.content.mpcontent.delivery import set_access_response_handler

from ..models import Embed


def _response_handler( request, access_session ):
    """
    Embed pages support head/body inclusion and the option to render the
    head and/or body as an MPF template.
    """
    log.debug_on() and log.debug("PROTECTED EMBED response: %s",
                            str(access_session))

    embed = Embed.objects.get_quiet( _provider_id=request.sandbox._provider_id,
                                    id=access_session['data'] )
    context = {
        'is_page_content': True,
        'embed': embed,
        }

    # Render the head and body text if requested
    render_context = make_context( context, request )
    if embed.head and embed.head_template:
        head_template = mpTemplate( embed.head )
        context['head_render'] = head_template.render( render_context )
    if embed.body and embed.body_template:
        body_template = mpTemplate( embed.body )
        context['body_render'] = body_template.render( render_context )

    return TemplateResponse( request, 'content/page/embed.html', context )

set_access_response_handler( Embed.access_type, _response_handler )
