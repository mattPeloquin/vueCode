#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utilities for collecting and combining output from tasks and jobs

    What a job does with output is controlled by the job's
    sub task and done functions. These methods support a default
    functionality that accumulates all sub task return values
    from cached output when all sub tasks have completed.
"""
from django.conf import settings

from .. import log
from ..utils import now
from .mp_async import mp_async
from .spooler import ASYNC_RETRY


JOB_INCOMPLETE = '__MPF_JOB_RUNNING__'
DEV_LOCAL_POLL = 1


@mp_async
def job_done( **kwargs ):
    """
    Task function run on spooler as default check for completed jobs.
    This does not do anything with the job process_output.
    """
    output = process_job_output_if_done( **kwargs )
    if output == JOB_INCOMPLETE:
        return ASYNC_RETRY

def process_job_output_if_done( **kwargs ):
    """
    Generic synchronous completion function for a job.
    Provides implementation for the done_fn task function run when
    the job task is executed.
    Returns job process_output if done, or JOB_COMPLETE if not.
    """
    job = kwargs['my_task']

    # If job expired, wipe out remaining task sessions
    if now() > job.expires:
        log.warning("JOB EXPIRED: %s", job)
        job.expired = True
        return job.process_output()

    log.info2("Checking job done: %s", job)
    remaining_tasks = job.cache.get_many( job.task_keys )

    if not remaining_tasks:
        log.debug("Job has no more tasks, so is complete: %s", job)
        return job.process_output()

    # DEV HACK - LOCAL thread simulation of SQS can't repost, so poll
    if not settings.MP_CLOUD:
        from time import sleep
        wait_count = 1
        while job.cache.get_many( job.task_keys ) and wait_count < 10:
            log.info("DEV - waiting for root job to complete: %s", job)
            sleep( DEV_LOCAL_POLL )
            wait_count += 1
        if wait_count < 10:
            return job.process_output()

    return JOB_INCOMPLETE

def task_output_key( session_key ):
    # Store sub task output based on task session key
    return '{}_output'.format( session_key )

def get_task_output( cache, task_session ):
    """
    Gets and removes a task's session output if it exists
    """
    output_key = task_output_key( task_session )
    output = cache.get( output_key )
    cache.delete( output_key )
    return output
