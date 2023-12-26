#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code run at the start of every Django worker
"""
import os
import re
import threading
from django.conf import settings

from mpframework.common import log
from mpframework.common.tasks import start_task_polling
from mpframework.common.tasks import start_bots


_SETUP_DELAY = 4.0


def process_startup():
    """
    Run at start of each process, after Django ready
    """
    thread = threading.current_thread()
    log.info("PROCESS STARTUP: %s-%s", os.getpid(), thread.name)

    # HACK - For dev ensure content model test data content types are fixed up
    if settings.MP_DEVWEB:
        from mpframework.content.mpcontent.models import BaseItem
        for item in BaseItem.objects.filter():
            item.downcast_type

    # uWSGI specific setup for spooler
    _setup_uwsgi( thread )

    # Start Process Update poller (creates new thread)
    # Unit testing handles this separtely, see process_update comments
    if not settings.MP_TESTING:
        from .process_update import start_process_update_polling
        start_process_update_polling()

def _setup_uwsgi( thread ):
    """
    Initialize uwsgi after short delay to avoid issues
    seen with startup timing.
    """
    def _delay():
        try:
            import uwsgi
            _test_for_valid_import = uwsgi.SPOOL_RETRY

            # Add poller threads and bots to spooler processes
            if uwsgi.i_am_the_spooler():
                start_task_polling()
                start_bots()

            for thread in threading.enumerate():
                _fixup_thread( uwsgi, thread )

        except ( ImportError, AttributeError ):
            # Allow polling and bots in dev environment
            if not settings.MP_TESTING:
                start_task_polling()
                if settings.MP_CLOUD:
                    start_bots()

    delay = threading.Timer( _SETUP_DELAY, _delay )
    delay.start()

def _fixup_thread( uwsgi, thread ):
    """
    Set thread names for more readable logging
    """
    if thread.name:
        old_name = thread.name

        if thread.name.startswith('uWSGI'):
            match = re.match( r'([a-z]+)([0-9]+)([a-z]+)([0-9]+)',
                                thread.name, re.I )
            if match:
                items = match.groups()
                thread.name = 'W{}T{}'.format( items[1], items[3] )

        elif uwsgi.i_am_the_spooler():
            if thread.name.startswith('MainThread'):
                thread.name = 'Spooler'

        if old_name != thread.name:
            log.info("Changed thread name %s: %s -> %s", os.getpid(),
                        old_name, thread.name)
    else:
        thread.name = 'NONAME'
