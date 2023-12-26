#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sandbox Events

    Handles long-term event tracking and notification for all sandbox events,
    which include user and system events related to the sandbox.

    FUTURE - add SMS support
    FUTURE - add per-sandbox support for configuring custom email templates
        to events for sending to CUSTOMERS, including matching content, PA, etc.
"""
from django.conf import settings
from django.dispatch import Signal

from . import log
from .email import send_email_sandbox


# Signals for extending event behavior
event_group = Signal()
event_data = Signal()


EVENT_SANDBOX = 'S'
EVENT_GROUP = 'G'
EVENT_DATA = 'D'


def sandbox_event( user, event_name, *args, **kwargs ):
    """
    Send system event notifications about user actions to site and
    group account admins.
    """
    if user.is_root and not settings.DEBUG:
        log.info("ROOT ignoring event: %s -> %s", user, event_name)
        return
    # Caller can note that they are already calling from a task, in
    # which case there's no need to create new tasks for email and DB
    is_task = kwargs.pop( 'already_task', False )
    log.info2("Event: %s -> %s", user, event_name)
    try:
        event = settings.MP_SANDBOX_EVENTS.get( event_name )
        if not event:
            log.error("UNKNOWN NOTIFY EVENT: %s", event_name)
            return
        sandbox = user.sandbox
        event['name'] = event_name

        title = kwargs.pop( 'title', event['title'].format( email=user.email ) )
        message = str(event['message']) % ((user.name,) + args)

        email_kwargs = {}
        if is_task:
            email_kwargs['priority'] = 'NOW'

        # Sandbox notifications
        if EVENT_SANDBOX in event['scope'] and event['level'] <= sandbox.notify_level:

            # Look for sandbox overrides based on email action
            send_to = sandbox.options['notify'][ event_name ]
            if not send_to:
                send_to = [ sandbox.email_staff ]
            if not isinstance( send_to, list ):
                send_to = [ send_to ]

            send_email_sandbox( sandbox, title, message,
                        to_emails=send_to, **email_kwargs )

        event_info = {
            'user': user,
            'event': event,
            'is_task': is_task,
            'title': title,
            'message': message,
            }

        # Group and data events handled in MPF extensions
        if EVENT_GROUP in event['scope']:
            event_group.send( sender=sandbox.pk, event_info=event_info, email_kwargs=email_kwargs )

        # Store event data
        if EVENT_DATA in event['scope']:
            event_data.send( sender=sandbox.pk, event_info=event_info )

    except Exception as e:
        log.exception("NOTIFY EVENT: %s -> %s", user, event_name)
        if settings.MP_DEV_EXCEPTION:
            raise
