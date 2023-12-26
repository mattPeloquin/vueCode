#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    SQS interface code code

    MPF uses SQS fifo queues -- NOT because ordering of mesages
    is critical, but to leverage the visibility of MessageGroups
    to partition load across sandboxes.

    Content-based dedupe should NOT be used in queues because it only
    considers the body, which if cache session key is fine but could
    also be the kwargs for a fn call which might not be unique.
"""
from django.conf import settings

from .. import log
from . import get_resource


def get_sqs():
    return get_resource('sqs')

def get_queue( name ):
    if settings.MP_CLOUD:
        try:
            sqs = get_sqs()
            if name.startswith('http'):
                return sqs.Queue( name )
            else:
                name = get_name( name )
                return sqs.get_queue_by_name( QueueName=name )
        except Exception as e:
            log.warning_quiet("SQS error getting: %s -> %s", name, e)

def get_name( name ):
    return '{}_{}.fifo'.format( settings.MP_PLAYPEN_SQS['NAME'], name )

def change_messages( queue, receipts, timeout ):
    """
    For now only changes seconds the fifo queue will block both making the
    message visible, and access to other messages in the message group.
    """
    try:
        return queue.change_message_visibility_batch( Entries=[
            {
                'Id': 'changeVizID' + str(n),
                'ReceiptHandle': receipt,
                'VisibilityTimeout': timeout,
                }
            for n, receipt in enumerate( receipts, 1 )
            ])
    except Exception as e:
        log.warning_quiet("SQS error change visibility: %s, %s -> %s",
                            queue, receipts, e)

def delete_messages( queue, receipts ):
    try:
        return queue.delete_messages( Entries=[
            {
                'Id': 'deleteID' + str(n),
                'ReceiptHandle': receipt,
                }
            for n, receipt in enumerate( receipts, 1 )
            ])
    except Exception as e:
        log.warning_quiet("SQS error delete: %s, %s -> %s",
                            queue, receipts, e)
