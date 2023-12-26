#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Asynchronous call and signal support

    Supports using uwsgi spooler (default) or threads to execute code
    asynchronously (typically outside of request-response).

    uwsgi spooling will be used if available (server) but will fall back
    to threads if not (local dev).

    NOTE - Python threads are limited by the GIL for each process, BUT
    operations that could cause contention with a resource (local sever
    or remote) need to manage access to the resources.
"""
import threading
from django.conf import settings
from django.db import connections

from .. import log
from ..deploy.server import get_uwsgi


uwsgi = get_uwsgi()


def mp_async( fn ):
    """
    Decorator that registers asynchronous functions for
    tasks, jobs and run_queue_function calls.

    Sets up for spooler processing if running on server; otherwise is noop for
    running on thread (usually local testing).

    RETURN VALUES for mp_async functions are NOT USED.
    Task processing will assume message/task is processed once function is called.
    If there is a failure with an asynchronous call worth retrying,
    it is up to the function to make that happen (i.e., repost the message).
    """
    fn._mp_async = True

    # Add to spooler function list under uwsgi
    if uwsgi:
        name = fn.__name__
        if name in _async_functions:
            raise Exception("ERROR async function conflict: %s" % name)
        _async_functions[ name ] = fn

    return fn

def is_async_fn( fn ):
    return getattr( fn, '_mp_async', False )

def get_async_fn( name ):
    return _async_functions.get( name )
_async_functions = {}


def run_routine_async( fn, *args, **kwargs ):
    """
    Local async spool/thread call wrapper, called from Tasks, which
    wrap all asynchronous processing.

    If available uwsgi spooling (vs. threading) will be used, with binary
    data passed between caller and spooler via spooler folder.
    """
    assert is_async_fn( fn ), "run_routine_async without @mp_async"
    # These are reserved kwargs that can't be used in async functions
    async_message = kwargs.pop( 'async_message', None )
    force_thread = kwargs.pop( 'force_thread', False )
    spool_priority = kwargs.pop( 'spool_priority', None )

    if settings.MP_TESTING and not settings.MP_TEST_USE_NORMAL_DB:
        # Can't use threading with Sqllite
        log.debug2("Calling async directly due to in-memory DB: %s", fn)
        fn( *args, **kwargs )
        return

    _run_async( fn, force_thread, async_message, spool_priority, *args, **kwargs )

def _run_async( fn, force_thread, async_message, spool_priority, *args, **kwargs ):
    """
    All task calls eventually run through here to be executed
    Verify whether spooler should and can be used to execute
    """
    use_spooler = uwsgi and not force_thread
    if use_spooler:
        if not _async_functions.get( fn.__name__ ):
            log.warning("SPOOL - No spool function, running in thread: %s", fn)
            use_spooler = False
    if use_spooler:
        from .spooler import call_with_spool
        call_with_spool( fn, async_message, spool_priority, *args, **kwargs )
    else:
        _CallWithThread( fn, *args, **kwargs ).start()


"""--------------------------------------------------------------------
    Thread Execution

    Although this can work in production, primarily for dev/test. It is not
    intended to scale; spooler much better across multiple processes.
"""
class _CallWithThread( threading.Thread ):

    def __init__( self, fn, *args, **kwargs ):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    def run( self ):
        log.debug("ASYNC thread start: %s -> %s", self, self.fn)
        try:
            # DEV HACK - simulate some SQS/spool delay for execution
            if settings.MP_DEVWEB:
                from time import sleep
                sleep( 2 )

            self.fn( *self.args, **self.kwargs )

        except Exception:
            log.exception_quiet("DURING ASYNC THREAD CALL")
            if settings.MP_TESTING:
                raise
        connections.close_all()
        log.debug2("ASYNC thread end: %s", self)


"""--------------------------------------------------------------------
    Asynchronous Django signal receiver class

    Work that is safe and reasonable to handle immediately on the same server
    can execute on spooler or on thread.
"""
class AsyncReceiver:

    def __init__( self, **kwargs ):
        self.force_thread = kwargs.pop( 'force_thread', False )
        self.connect( **kwargs )

    def __call__( self, sender, **kwargs ):
        kwargs['sender'] = sender
        try:
            _run_async( self.handle_signal, self.force_thread, None, None, **kwargs )

        except Exception:
            log.exception_quiet("AsyncReceiver call: %s", self.handle_signal)

    def connect( self, **kwargs ):
        # Override the this to connect to signals
        raise Exception("Base Receiver class called")

    @staticmethod
    def handle_signal( **kwargs ):
        # Override the this method to handle receiving
        # Sender will be moved into kwargs
        raise Exception("Base Receiver class called")
