#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Task and job testing support
"""
from time import sleep

from .. import log
from . import mp_async
from . import run_queue_function
from .job import Job
from .output import process_job_output_if_done
from .output import JOB_INCOMPLETE
from .spooler import ASYNC_RETRY


def test_task( message, **kwargs ):
    """
    Post SQS messages to test task processing
    """
    priority, cache, kwargs = _attr_setup( **kwargs )
    fn = kwargs.pop( 'fn', _test_task )
    run_queue_function( fn, 'TEST_TASK', my_priority=priority,
                message=message, cache=cache )

@mp_async
def _test_task( message='', **kwargs ):
    task = kwargs.pop('my_task')
    log.info("===> TEST TASK: %s -> %s", task, message )
    sleep_time = kwargs.get( 'sleep_time', 1 )
    sleep( sleep_time )

def test_job( message, **kwargs ):
    """
    Create test job hierarchy sub jobs and tasks at each node
    """
    priority, cache, kwargs = _attr_setup( **kwargs )
    max_depth = int( kwargs.pop('depth', 1) )
    node_jobs = int( kwargs.pop('jobs', 1) )
    num_tasks = int( kwargs.pop('tasks', 1) )
    task_fn = kwargs.pop( 'fn', _test_job_task )

    total_tasks = (node_jobs ** (max_depth-1) ) * num_tasks

    # Sanity check
    if total_tasks > 5000:
        log.info("===> TEST JOB TOO BIG: %s", total_tasks )
        return
    log.info("===> START TEST JOB with %s tasks", total_tasks )

    root_job = Job( 'TASK_TEST', { 'message': message }, my_cache=cache,
                done_fn=_test_job_done, message=message )

    def create_nodes( parent, depth ):
        """
        Test a nested job structure that allows parallel execution of
        of sub-jobs in different groups.
        """
        if depth < max_depth:
            group = 'TASK_TEST{}'.format( depth )
            for n in range( node_jobs ):
                message = '{}-SUBJOB: {}'.format( parent.data['message'], n )
                job = Job( group, { 'message': message }, my_parent=parent,
                                my_priority=priority )
                create_tasks( job )
                create_nodes( job, depth + 1 )
                job.start()

    def create_tasks( job ):
        for n in range( num_tasks ):
            job.add_task( task_fn, number=n )

    create_nodes( root_job, 1 )
    root_job.start()

@mp_async
def _test_job_task( number, **kwargs ):
    task = kwargs['my_task']
    rv = "{}-TASK: {}".format( task.job.data['message'], number )
    log.info("===> JOB TASK executed: %s", rv )
    task.finalize( [rv] )

@mp_async
def _test_job_done( message, **kwargs ):
    output = process_job_output_if_done( **kwargs )
    if output == JOB_INCOMPLETE:
        return ASYNC_RETRY
    log.info("====>  TEST JOB COMPLETED: %s  <====", message )
    log.info( output )

def _attr_setup( **kwargs ):
    priority = kwargs.pop( 'p', 'HS' )
    cache = kwargs.pop( 'c', 'session' )
    if cache == 'NONE':
        cache = ''
    return  priority, cache, kwargs
