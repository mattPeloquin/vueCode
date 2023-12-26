#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Polling and dispatch for MPF prioritized task queues

    Sets up poller(s) that check for SQS messages using long polling
    within thread(s). Tasks are extracted from messages and executed.

    THE GOAL -> Durably time-shift and partition work across many
    multi-tenant clients vs. maximizing performance of one piece of work
    via parallell execution.

    MPF Task queues are SQS FIFO queues NOT because ordering or single
    delivery is critical, but rather to use MessageGroups to partition
    load across sandboxes and different types of work.
    The visibility support provided by MessageGroups provides a simple
    mechanism for distributing tenant work across many consumers.
    The high-scalability concerns of fifo queues aren't relevant unless
    concurrent loading exceeds 20K, in which case queues could be partitioned
    for types of work (e.g., reporting) or a different approach used.

    Tasks are normally processed asynchronously by the local spooler,
    with the SQS message deleted upon completion.
    TIMEOUTS FOR MESSAGE VISIBILITY NEED TO BE CONFIGURED APPROPRIATELY

    There is also an option to execute tasks immediately in these poller
    threads. This should be used sparingly, as it blocks the poller.

    SQS messages are normally deleted after task is processed; if failure,
    it is up to the task to either recreate the message in the queue,
    or not worry about it.

    There are 'unsafe' spooler priority options that delete messages before
    the task is processed, which will not block a message group so
    allow for parallel execution of work.
    These should only be used for independent tasks that must be processed
    immediately as they may block other message groups.
    NOTE - EXECUTION OF THESE TASKS WON'T BE GUARANTEED

    FUTURE - consider overhead optimizations like placing more
    than one SQS message into a spooler task based on big/small indicator
"""
import os
import json
import threading
from django.conf import settings

from .. import log
from ..aws import sqs
from ..deploy.server import mp_shutdown
from . import get_module_name
from .spooler import spool_queue_task_count
from .task import Task


# Map SQS queue names to MPF priorities
_priorities = {
    'HI': 'HIGH',   # Execute immediately, delete message upon completion
    'HS': 'HIGH',   # Spool with message delete upon completion
    'HSU': 'HIGH',  # Spool, delete message before completion
    'MI': 'MED',
    'MS': 'MED',
    'MSU': 'MED',
    'LS': 'LOW',
    }

# Queue settings are defined in config
_queues = settings.MP_UWSGI.get( 'SPOOL_QUEUES', {} )
for name, queue in _queues.items():
    queue['name'] = name
    queue['message_groups'] = []
    groups = queue.get('TASK_GROUPS')
    queue['message_groups'] = groups if groups else [ Task.ALL_GROUP ]
    queue['receive_options'] = {
        'MessageAttributeNames': ['All'],
        'WaitTimeSeconds': queue['LONG_POLL'],
        'VisibilityTimeout': queue['VISIBILITY_TIMEOUT'],
        'MaxNumberOfMessages': queue.get( 'MESSAGES', 1 ),
        }


def start_task_polling():
    """
    Start poll threads based on configuration.
    When a task is received from distributed queue it may be executed within
    the poller thread, or placed on local spooler file queue.
    """
    pollers = settings.MP_UWSGI.get( 'SPOOL_POLLERS', {} )
    for name, poller in pollers.items():
        names = poller['QUEUES']
        freq = poller['FREQ']
        thread = threading.Timer( 0, _poll_worker, args=[ names, freq ] )
        thread.name = name
        log.info("Starting %s poll thread every %s on %s: %s", names, freq,
                    os.getpid(), thread.name)
        thread.start()

def delete_message( message_info ):
    """
    Delete a message that was pulled from SQS and handed to another
    place for processing (like spooler).
    """
    queue = sqs.get_queue( message_info['queue_url'] )
    sqs.delete_messages( queue, [ message_info['receipt_handle'] ] )

def get_queue( priority ):
    """
    Get SQS queue based on priority
    """
    return sqs.get_queue( _priorities[ priority ] )

def _poll_worker( names, freq ):
    """
    Message queue polling thread worker.
    Makes round robin requests of each queue in names. Sleeps between
    requests and blocks if long-polling is enabled.
    Keeps tracks of tasks in local spooler for each polling call.
    """
    queues = {}
    for name in names:
        queue = _queues.get( name )
        if queue:
            queue = queue.copy()
            connection = sqs.get_queue( name )
            if not connection:
                if settings.MP_CLOUD:
                    log.warning("SQS POLLER could not connect to SQS queue: %s", name)
                continue
            queue['client'] = connection
            queues[ name ] = queue
    log.info2("Starting SQS poller: %s", names)
    log.debug("SQS poller: %s", queues)

    while not mp_shutdown().started():
        try:
            # Get spooler file lengths to determine whether to poll
            queues_to_poll = {}
            task_counts = spool_queue_task_count()
            for name, queue in queues.items():
                if task_counts[ name ] < queue.get( 'FULL_THRESHOLD', 1 ):
                    queues_to_poll[ name ] = queue
                else:
                    log.info3("SQS skipping poll, spooler full: %s -> %s",
                                name, task_counts[ name ])

            for name, queue in queues_to_poll.items():
                if mp_shutdown().started():
                    continue
                log.info4("Checking SQS queue: %s", name)

                # Handle messages - BLOCKS HERE if LONG_POLL over 0
                messages = queue['client'].receive_messages(
                            **queue['receive_options'] )
                if messages:
                    _process_messages( messages, queue )

        except Exception:
            log.exception("SQS POLL FAIL: %s", names)

        mp_shutdown().wait( freq )

    log.debug("Exiting SQS poller: %s", names)

def _process_messages( messages, queue ):
    """
    Handle any messages from polling either directly or in spooler.
    """
    for message in messages:
        if mp_shutdown().started():
            # Don't try to reset message, accept visibility timeout
            return
        log.debug2("Processing SQS message: %s -> %s", queue, message)
        try:
            handle = True
            # Message versioning (used if message interface changes)
            version = message.message_attributes.get('mpVersion').get('StringValue')
            server_version = settings.MP_PLAYPEN_SQS['VERSION']
            if version != server_version:
                handle = False
            # Check that message matches groups server will handle
            if handle:
                groups = queue['message_groups']
                if not Task.ALL_GROUP in groups:
                    if not message.attributes:
                        handle = False
                    else:
                        group = message.attributes.get('MessageGroupId')
                        if not any( group.startswith( mg ) for mg in groups ):
                            handle = False
            if not handle:
                log.info3("Skipping message: %s -> %s, %s -> %s", queue,
                            version, server_version, message )
                # Tell queue message should be made available to others
                message.change_visibility( VisibilityTimeout=0 )
                return

            priority = message.message_attributes.get('mpPriority').get('StringValue')
            message_handler = _task_types.get( priority )

            delete = message_handler( message )

        except Exception:
            log.exception("SQS MESSAGE: %s -> %s", queue, message)
            # Assume message was bad and shouldn't be tried again
            delete = True
        # Delete if message executed
        if delete:
            message.delete()

def _execute_task( message, immediate=False, block_message=True ):
    """
    Process SQS message according to MPF conventions.
    Returns True if message should be deleted.
    """
    handler = message.message_attributes.get('mpHandler').get('StringValue')
    log.debug2("EXECUTE_TASK message: %s", handler)

    # Setup kwargs from message
    kwargs = json.loads( message.body )

    if immediate:
        kwargs['immediate_task'] = True
    elif block_message:
        kwargs['async_message'] = {
            'delete_message_fn': get_module_name( delete_message ),
            'queue_url': message.queue_url,
            'receipt_handle': message.receipt_handle,
            }

    # Execute task (either on spooler or directly, depending on handler)
    spooled = Task.execute( handler, kwargs )
    return not block_message or not spooled

# Map priorities to task handlers
_task_types = {
    'HS': _execute_task,
    'MS': _execute_task,
    'LS': _execute_task,
    'HI': lambda m: _execute_task( m, True ),
    'MI': lambda m: _execute_task( m, True ),
    'HSU': lambda m: _execute_task( m, True, False ),
    'MSU': lambda m: _execute_task( m, False, False ),
    }
