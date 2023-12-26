#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Spooling execution

    Spooling is used as a buffer for asynchronous processing from
    external message queues. Thus the spooler on a particular process
    is not responsible for retries; if something fails, it removes it
    from spooler processesing to be dealt with by message queue.

    Spooling executes a function in spooler processes from values stored
    on disk, so the function must be registered at process load so the
    spooler process knows what function to call based on the name.
    THUS mp_async FUNCTIONS NEED UNIQUE NAMES

    MPF wraps spooler handling vs using the uwsgi spool decorators
    to provide more control over process and support async calls via
    thread vs spooler for local dev (and as a possible execution option).

    When a spooler process wakes up, it will read ALL tasks in the
    spool folders and then execute ALL of them.
    When multiple spooler processes are used, they will each grab all
    tasks that are present at that time.
    All tasks are placed in numbered sub-folders to use the uwsgi priority
    system to allow higher priority tasks to execute first.
    This also allows determining how many tasks of different priority
    are in the queue.

    Dill is used to pickle arguments since it is more robust than Pickle
    and performance isn't critical.
    SECURE - See discussion of pickle in common/cache/call_cache.py

    SPOOL_SLEEP_AFTER is option to force spooler to take a break
    after a successful task to avoid triggering autoscale.
"""
import os
import dill
from time import sleep
from django.db import close_old_connections
from django.db import reset_queries
from django.db.utils import OperationalError
from django.conf import settings

from .. import log
from ..db import db_connection_retry
from ..deploy import load_module_attr
from ..deploy.paths import home_path
from ..deploy.server import get_uwsgi
from ..utils.file import create_local_folder
from .mp_async import get_async_fn


dill.settings['byref'] = True

# Will only be valid if running under uwsgi
uwsgi = get_uwsgi()

# Map spool retry to value that is easier to import and
# will be available if uwsgi not loaded
ASYNC_RETRY = uwsgi.SPOOL_RETRY if uwsgi else -1

# HACK - Map queue polling priority onto which folders should be checked
# for spooled tasks when determining whether to pull messages
# and create spooler priority sub-folders on startup
_queue_folders = {
    1: [ 'HIGH' ],
    2: [ 'MED', 'LOW' ],
    }
if uwsgi:
    _spool_folders = [ home_path( 'uwsgi', 'spooler', str(folder) ) for
                        folder in sorted( _queue_folders ) ]
    for folder in _spool_folders:
        create_local_folder( str(folder) )

# Byte keys to use with spooler
_fn_name = 'fn_name'.encode()
_priority = 'priority'.encode()
_body = 'body'.encode()


def call_with_spool( fn, async_message, spool_priority=None, *args, **kwargs ):
    """
    Pack up the function and enqueue for spooler execution.
    spool wants all keys and values of dict to be bytes.
    """
    assert uwsgi
    task = {}
    task[ _fn_name ] = fn.__name__.encode()
    if spool_priority not in _queue_folders:
        spool_priority = 2
    task[ _priority ] = str( spool_priority ).encode()
    log.debug("ASYNC spool enqueue: priority(%s) %s -> %s",
                spool_priority, fn.__name__, args and args[0])

    # Put packed arguments directly in the spool file
    body = {}
    body['_args_'] = args
    body['_kwargs_'] = kwargs
    body['_message_'] = async_message
    task[ _body ] = dill.dumps( body )

    uwsgi.spool( task )

def spool_queue_task_count():
    """
    Count the number of spool files (tasks) present in each spool folder
    AND any higher priority folders in front of it.
    Returns map of queue names with counts of total spool task backlog
    at each priority level.
    This isn't critical synchronization, so race conditions are accepted.
    """
    rv = {}
    if uwsgi:
        try:
            # HACK - Assumes numeric folder names as per uwsgi spooler.
            file_counts = []
            for folder in sorted( _queue_folders ):
                files = os.listdir( _spool_folders[ folder-1 ] )
                file_counts.append( len(files) )
                if len(file_counts) > 1:
                    file_counts[-1] += file_counts[-2]
            for folder in sorted( _queue_folders ):
                for queue in _queue_folders[ folder ]:
                    rv[ queue ] = file_counts[ folder-1 ]
        except OSError as e:
            log.warning("Spool tasks check failed (no folders?): %s", e)
    return rv

def spool_breathe( loop_counter=None ):
    """
    Sleep in a spool process to throttle CPU time
    """
    if settings.MP_WSGI:

        # For loops only sleep on increment
        if loop_counter:
            multiple = settings.MP_UWSGI.get('SPOOL_BREATHE_EVERY')
            if multiple and loop_counter % multiple:
                return

        sleep_time = settings.MP_UWSGI.get('SPOOL_BREATHE')
        if sleep_time:
            log.debug2("Spool breathe: %s", sleep_time)
            sleep( sleep_time )

@db_connection_retry
def spool_handler( task ):
    """
    Uwsgi calls to process spool tasks
    Can only execute appropriate registered async functions; function is looked up
    by name that was stored at startup with @mp_async decorator.
    If the async processing fails unexpectedly, log and remove that spool item
    by ensuring SPOOL_OK return.
    """
    try:
        # Make logging count of DB calls accurate
        reset_queries()

        # Body comes back as a str key, while fn_name is still bytes - go figure
        name = task[ _fn_name ].decode()
        body = dill.loads( task['body'] )

        fn = get_async_fn( name )
        log.debug2("ASYNC spool start: %s", fn)

        status = fn( *body.get('_args_'), **body.get('_kwargs_') )

        # Functions should return ASYNC_RETRY if they want a retry,
        # otherwise the message is removed from the queue
        if status != ASYNC_RETRY:
            message = body.get('_message_')
            if message:
                delete_fn = message.get('delete_message_fn')
                if delete_fn:
                    delete_fn = load_module_attr( delete_fn )
                    delete_fn( message )

        log.debug("ASYNC spool %s -> %s", name, status)

    except OperationalError:
        # Most likely DB connection needs reset, let caller manage
        raise
    except Exception:
        log.exception_quiet("DURING SPOOL CALL")

    # Close any expired connections
    close_old_connections()

    # Optionally force sleep to ensure long-running jobs don't
    # run back to back without pause
    sleep( settings.MP_UWSGI.get('SPOOL_SLEEP_AFTER', 0) )

    # ALWAYS return ok to uwsgi, so it will remove the item; any retries
    # are handled at the message queue level
    return uwsgi.SPOOL_OK
