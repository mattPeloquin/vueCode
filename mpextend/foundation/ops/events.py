#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Store events in Dynamo DB
"""
from django.dispatch import receiver

from mpframework.common import log
from mpframework.common.aws.dynamo import get_dynamo_table
from mpframework.common.events import event_data
from mpframework.common.utils import now
from mpframework.common.utils.file import unique_name
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function


@receiver( event_data )
def handle_event_data( **kwargs ):
    """
    Called by the sandbox event mechanism to store event data
    """
    event_info = kwargs.get('event_info')
    event = event_info.get('event')
    user = event_info.get('user')
    sandbox = user.sandbox

    # Use alternate to DB id for visitors
    user_id = user.pk or user.current_ip

    msg = f"{ event_info['title'] }: { event_info['message'] }"

    # HACK - until a more general idea of group is needed, get any
    # group account ID and use that
    from mpextend.product.account.utils import get_ga
    ga = get_ga( user )
    group_id = ga.pk if ga else 'all'

    if event_info['is_task']:
        _log_event( sandbox.pk, user_id, user.email, group_id,
                    event['name'], msg )
    else:
        run_queue_function( _log_event_task, sandbox, sandbox_id=sandbox.pk,
                    user_id=user.pk, user_email=user.email, group_id=group_id,
                    event=event['name'], data=msg )

def _log_event( sandbox_id, user_id, user_email, group_id, event, data ):
    """
    Store the even in dynamoDB
    """
    event_hash = f'{ sandbox_id }#{ event }#{ user_id }'
    item = {
        'event_hash': event_hash,
        'datetime': str( now() ),
        'event': str( event ),
        'sandbox_id': str( sandbox_id ),
        'user_id': str( user_id ),
        'group_id': str( group_id ),
        'email': str( user_email ),
        'data': str( data ),
        }
    log.debug("Saving sandbox event: %s", item)

    table = get_dynamo_table('events')
    if table:
        table.put_item( Item=item )

@mp_async
def _log_event_task( **kwargs ):
    """
    Task for update user item data on first usage
    """
    kwargs.pop('my_task')
    sandbox_id = kwargs.pop('sandbox_id')
    user_id = kwargs.pop('user_id')
    user_email = kwargs.pop('user_email')
    group_id = kwargs.pop('group_id')
    event = kwargs.pop('event')
    data = kwargs.pop('data')
    _log_event( sandbox_id, user_id, user_email, group_id, event, data )
