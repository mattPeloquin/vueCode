#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LiveEvent view support
"""
from django.http import HttpResponse
from django.template import Context
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from mpframework.common import log
from mpframework.common.template import mpTemplate
from mpframework.common.utils.http import attachment_string
from mpframework.content.mpcontent.delivery import set_access_session
from mpframework.content.mpcontent.delivery import set_access_response_handler
from mpextend.content.proxy.delivery import proxy_access_session
from mpextend.common.ics import calendar_event

from ..models import LiveEvent


@never_cache
def _response_handler( request, access_session ):
    """
    LiveEvent pages support several different scenarios from pre-defined
    templates, to custom templates, to custom page HTML based
    on the event type and configuration options.

    Querystring options of the content access are used for different
    access to the content:
        add_to_calender - returns an ics file
    """
    log.debug_on() and log.debug("PROTECTED EVENT response: %s",
                            str(access_session))

    event = LiveEvent.objects.get_quiet( _provider_id=request.sandbox._provider_id,
                                            id=access_session['data'] )

    # Provide calendar invite if requested
    if request.GET.get('add_to_calendar') and event.is_active():
        event = _calendar_event( request, event )
        if event:
            response = HttpResponse( event.to_ical(), content_type='text/calendar' )
            filename = "{}_{}.ics".format( request.sandbox.name, event.name )
            response['content-disposition'] = attachment_string( filename )
            return response

    context = {
        'is_page_content': True,
        'event': event,
        }
    opts = event.proxy_options
    styled = True

    if event.is_open():
        # Proxy the event link into an iframe
        if event.is_proxy:
            styled = False
            event_template = 'content/page/iframe_url.html'
            new_session = proxy_access_session( access_session, 'event_proxy' )
            set_access_session( new_session )
            context.update({
                'content_mptype': 'liveevent',
                'content_id': access_session['data'],
                'content_url': access_session['url'],
                })
        # Show invite in a page
        else:
            event_template = opts.get( 'template.open', 'event_open' )
    # Show the event complete page, with download if present
    elif event.is_closed():
        event_template = opts.get( 'template.closed', 'event_closed' )
    # Show the countdown page
    else:
        event_template = opts.get( 'template.before', 'event_before' )

    context.update({
        'page_base': '_base/pages/style.html' if styled else '_base/page_bare.html',
        'event_template': event_template,
        'calendar_invite_url': request.path + '?add_to_calendar=t',
        })
    return TemplateResponse( request, 'content/page/event.html', context )

set_access_response_handler( LiveEvent.access_type, _response_handler )

def _calendar_event( request, event ):
    """
    Try to create a calendar event from the given live event
    """
    opts = {
        'organizer': {
            'name': request.sandbox.name,
            'email': request.sandbox.email_support,
            },
        'attendees': [{
            'name': request.user.name,
            'email': request.user.email,
            }],
        }
    # Render invite body
    context = {
        'event': event,
        'event_url': event.get_access_url( request ),
        }
    template = mpTemplate( opts.get( 'template.invite', 'event_invite' ) )
    opts['description'] = template.render( Context( context ) )

    return calendar_event( event.name, event.event_starts,
                            event.event_ends, **opts )

@never_cache
def _proxy_response_handler( request, access_session ):
    """
    For proxied events, after iframe call makes first call to the proxy,
    follow-on responses sent here.
    """
    event = LiveEvent.objects.get( _provider_id=request.sandbox._provider_id,
                                    id=access_session['data'] )
    log.debug("PROTECTED EVENT proxy response: %s -> %s", event, access_session)
    return event.get_proxy_response( request )

set_access_response_handler( 'event_proxy', _proxy_response_handler )
