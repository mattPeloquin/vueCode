#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for creating ICS meeting invites
"""
import uuid
from icalendar import Calendar
from icalendar import Event
from icalendar import vCalAddress
from icalendar import vText
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils import now


_CALENDAR_METADATA ={
    'prodid': '-//' + settings.MP_UI_TEXT.get('root_name') + '//mpf',
    'version': '2.0',
    }


def calendar_event( summary, start, end, **kwargs ):
    """
    Create an ICS calendar object that can be converted to a file
    """
    try:
        rv = Calendar()
        for key, value in _CALENDAR_METADATA.items():
            rv.add( key, value )

        event = _event( summary, start, end, **kwargs )
        rv.add_component( event )

    except Exception:
        log.exception("ICS CALENDAR %s", kwargs )
        if settings.MP_DEV_EXCEPTION:
            raise
    return rv


def _event( summary, start, end, **kwargs ):
    """
    Create an ICS calendar object that can be converted to a file
    """
    rv = Event()
    # Minimum items
    rv.add( 'summary', summary )
    rv.add( 'dtstart', start )
    rv.add( 'dtend', end )

    # Optional items
    if kwargs.get('description'):
        rv['description'] = vText( kwargs.get('description') )
    if kwargs.get('location'):
        rv['location'] = vText( kwargs.get('location') )
    if kwargs.get('organizer'):
        rv['organizer'] = _address( **kwargs.get('organizer') )
    if kwargs.get('attendees'):
        for attendee in kwargs.get('attendees'):
            rv.add( 'attendee', _address( **attendee ), encode=0 )

    rv.add( 'dtstamp', now() )
    rv['uid'] = str(uuid.uuid4()) + '@mpf'
    return rv

def _address( **kwargs ):
    """
    Expects email to be passed, and then adds optional parameters
    """
    rv = vCalAddress( 'MAILTO:' + kwargs['email'] )
    if kwargs.get('name'):
        rv.params['cn'] = vText( kwargs.get('name') )
    rv.params['ROLE'] = vText( kwargs.get( 'role', 'REQ-PARTICIPANT' ) )
    return rv
