#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Server process and thread support
    Threads MUST use mp_shutdown started/wait if polling.
"""
import os
import atexit
import threading

from .. import log
from . import UWSGI_WORKER_PRE_SHUTDOWN
from . import UWSGI_SPOOLER_PRE_SHUTDOWN


#--------------------------------------------------------------
# Shared uWsgi support

def get_uwsgi():
    """
    The uWSGI server will expose the uwsgi module if running in it
    """
    try:
        import uwsgi
        _test_for_valid_import = uwsgi.SPOOL_RETRY
        return uwsgi
    except ( ImportError, AttributeError ):
        return

def uwsgi_register():
    """
    Signal handling can be used between processes, but is used by the
    for signaling from command line:
        uwsgi --signal [socket],[signal_number]
    """
    uwsgi = get_uwsgi()

    uwsgi.atexit = mp_atexit

    # Register pre-shutdown flag with workers and spooler
    uwsgi.register_signal( UWSGI_WORKER_PRE_SHUTDOWN,
                            'workers', mp_pre_shutdown )
    uwsgi.register_signal( UWSGI_SPOOLER_PRE_SHUTDOWN,
                            'spooler', mp_pre_shutdown )

"""-------------------------------------------------------------
    Shutdown support
    Ensure graceful shutdown, particularly with polling threads.
"""

def mp_shutdown():
    return _shutdown

def mp_atexit( *args ):
    """
    Idempotent call used to shutdown the server. Uses both Python
    atexit and uwsgi exit support to signal shutdown event and
    wait for threads to cleanup.
    """
    log.debug("Calling mp_atexit: %s -> %s", os.getpid(), args)
    if not _shutdown.started():
        _shutdown.shutdown()
        log.debug("SHUTDOWN waiting for threads: %s -> %s", os.getpid(), args)
    # Only wait for threads in one call
    if not _shutdown.exit_wait:
        _shutdown.exit_wait = True
        for thread in _shutdown.threads.values():
            thread.join()

@atexit.register
def _python_exit( *args ):
    mp_atexit( *args )

class Shutdown:

    def __init__( self ):
        self._shutting_down = False
        self._shutdown_event = threading.Event()
        self.threads = {}
        self.exit_wait = False

    def started( self ):
        """
        Check whether shutdown is occurring, which may be triggered
        from pre-shutdown or actual shutdown.
        """
        return self._shutting_down

    def wait( self, timeout ):
        """
        Threads should call this instead of sleep to:
          - Register for process join on terminate
          - Wait on shutdown event vs. sleeping
        """
        thread = threading.current_thread()
        log.timing3("WAIT: %s -> %s", timeout, thread.name)
        self.threads[ thread.name ] = thread
        return self._shutdown_event.wait( timeout )

    def shutdown( self ):
        log.debug2("Shutting down: %s -> %s", os.getpid(), self)
        self._shutting_down = True
        self._shutdown_event.set()

# Share across threads
_shutdown = Shutdown()

def mp_pre_shutdown( *args ):
    # Can use used with signals and MPF commands to start shutdown
    # while some other actions need to occur
    log.debug("PRE SHUTDOWN: %s -> %s", os.getpid(), args)
    _shutdown.shutdown()

#--------------------------------------------------------------
# Adding global data to thread local storage
# Only used for limited server configuration information

_thread_local = threading.local()

def get_thread_local( name, default_fn ):
    """
    Provide a lazy default that is only used if needed, in
    case it is expensive.
    """
    log.detail3("Get thread local: %s", name)
    if not hasattr( _thread_local, name ):
        set_thread_local( name, default_fn() )
    return getattr( _thread_local, name, None )

def set_thread_local( name, value ):
    log.debug2("Set thread local: %s -> %s", name, value)
    setattr( _thread_local, name, value )
