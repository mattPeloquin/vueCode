#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Asynchornous task processing

    Supports various configurations for function/task/job/bot
    processing for production (distributed) and dev (single server).

    Although built for SQS and uwsgi spooling, the processing
    model could be implemented with other mechanisms.
"""

def get_module_name( obj ):
    """
    Given python obj, try to return name
    """
    try:
        return obj.__module__ + '.' + obj.__name__
    except Exception:
        from mpframework.common import log
        from django.conf import settings
        log.exception_quiet("GET MODULE ERROR: %s", obj)
        if settings.MP_TESTING:
            raise

from .mp_async import mp_async
from .queue_send import send_queue_task
from .queue_send import run_queue_function
from .poller import start_task_polling
from .spooler import spool_handler
from .spooler import spool_breathe

from .task import Task
from .job import Job

from .bots import Bot
from .bots import start_bots
