#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Each process polls for changes to options that require
    the process to rerun initialization code (e.g., logging).
"""
from threading import Timer
from django.conf import settings
from django.db import connections

from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.common.cache.clear import invalidate_key
from mpframework.common.deploy.server import mp_shutdown
from mpframework.common.utils import now

from .logging_setup import set_logging


_updaters = {
    'set_logging': ( set_logging, None ),
    }
POLL_FREQ = settings.MP_SERVER['PROCESS_UPDATE_POLL']


def start_process_update_polling():
    """
    Bootstrap polling loop used to update process
    """
    thread = Timer( 0, _update_process )
    thread.name = 'update'
    thread.start()
    return thread


def _lastupdate_str( fn_name ):
    """
    Provide time-based unique marker for last distributed update.
    """
    return fn_name + str( now() )

def _lastupdate_keyfn( fn_name ):
    """
    Use one cache entry per fn_name without versioning.
    """
    return 'process_update_{}'.format( fn_name ), ''

@cache_rv( keyfn=_lastupdate_keyfn, keyname='', punch_through=True )
def update_processes_for_workfn( fn_name ):
    """
    Overwrite the lastupdate value in the cache, which will cause
    all processes to run their updaters on the next poll.
    """
    return _lastupdate_str( fn_name )

@cache_rv( keyfn=_lastupdate_keyfn, keyname='' )
def _get_lastupdate( fn_name ):
    """
    Checks the currently cached value, which may have been updated
    by another process, indicating this process needs to update.
    """
    return _lastupdate_str( fn_name )


def _update_process():
    """
    Thread main for update functionality
    """
    log.info2("UPDATE PROCESS starting: %s", _updaters)

    while not mp_shutdown().started():
        _check_updaters()
        mp_shutdown().wait( POLL_FREQ )

    log.debug("UPDATE PROCESS exiting")

def _check_updaters():

    # For each registered work function
    for name, updater in _updaters.items():
        lastupdate_system = _get_lastupdate( name )

        # If the local flag stored in the module for this process
        # is different from the cached value, assume update is necessary
        fn, lastupdate_local = updater
        needs_update = not ( lastupdate_local == lastupdate_system )

        # Execute the work function if update needed
        if needs_update:
            try:
                log.debug("UPDATE PROCESS: %s", name)

                fn()

                # Set local indication of the last time
                _updaters[ name ] = ( fn, lastupdate_system )

            except Exception:
                log.exception("update_process work function: %s", name)
        else:
            log.detail3("_update_process skipping %s, sys=%s, local=%s",
                        fn.__name__, lastupdate_system, lastupdate_local)

    connections.close_all()
