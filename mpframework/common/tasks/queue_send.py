#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Post work to queue
    Support for posting tasks and wrapping a function call in a task.
"""
import json
from django.conf import settings

from .. import log
from ..utils import json_dump
from ..utils import get_random_key
from .task import Task
from .poller import get_queue


def run_queue_function( fn, group, *args, **kwargs ):
    """
    Wrap a function in a Task with default settings and execute
    The fn must:
        - BE LOADABLE BY SPOOLER FROM IT'S MODULE
        - Use an @mp_async decorator
        - Handle/ignore my_task kwargs
        - Have dill picklable arguments for SQS and async pathways
          SECURE - See discussion of pickle in common/cache/call_cache.py
    kwargs has reserved options, in addition to my_task kwargs:
        my_args passes args to fn
        my_priority sets SQS queue priority
    """
    if args:
        # If args are used, fn must know how to unpack _args
        kwargs.update({
            'my_args': args,
            })
    # Post wrapped function to queue to execute inside a task
    send_queue_task( Task( fn, group, **kwargs ) )

def send_queue_task( task, resend=False ):
    """
    Send task message to SQS
    """
    # The message body will have cache session or message itself
    body = json_dump( task.put_info() )
    handler_name = task.handler_name

    # DEV HACK - Start Task here for non SQS run/test
    if not settings.MP_CLOUD:
        Task.execute( handler_name, json.loads( body ) )
        return

    queue = get_queue( task.priority )
    if queue:
        attr = {
            'mpPriority': { 'StringValue': task.priority, 'DataType': 'String' },
            'mpHandler': { 'StringValue': handler_name, 'DataType': 'String' },
            'mpVersion': { 'StringValue': settings.MP_PLAYPEN_SQS['VERSION'], 'DataType': 'String' },
            }

        # Use task key, since semantics for duplicate are a task is
        # only ever created once; if resend, force new one to be considered
        dupe_id = get_random_key() if resend else task.key

        options = {
            'MessageBody': body,
            'MessageAttributes': attr,
            'MessageDeduplicationId': dupe_id,
            'MessageGroupId': task.message_group,
            }

        response = queue.send_message( **options )

        log.debug("Sent SQS message: %s -> %s",
                    response.get('MessageId'), task)
    else:
        log.error_quiet("ERROR SQS SEND MESSAGE %s", task)
