#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Add group account event handling
"""
from django.dispatch import receiver

from mpframework.common.events import event_group
from mpframework.common.email import send_email_sandbox

from ..utils import get_ga


@receiver( event_group )
def handle_event_group( **kwargs ):
    """
    Called by the sandbox event mechanism for registered group events.
    """
    event_info = kwargs.get('event_info')
    user = event_info.get('user')

    ga = get_ga( user )
    if ga:
        event = event_info.get('event')
        if event['level'] <= ga.notify_level:
            send_to = []
            for admin in ga.admins.all():
                send_to.append( admin.user.email )
            if send_to:
                email_kwargs = kwargs.get('email_kwargs')
                send_email_sandbox( user.sandbox, event_info['title'],
                            event_info['message'], to_emails=send_to,
                            **email_kwargs )
