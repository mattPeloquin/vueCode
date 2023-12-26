#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF Job

    A job is special task that defines a set of tasks that represent
    a coherent set of work. A job task:

     - Has a set of tasks that reference it
     - Has task function that checks for completion handles finalization
     - Can have read-only data shared across its tasks
     - Can build a hierarchy of jobs

    Jobs have NO support for state or dependency order of sub-tasks and child jobs;
    Each job and task run within a hierarchy of jobs must be able to run independently
    and not rely on completion of other tasks within job hierarchy.

    The process_job_output_if_done function will check whether all registered sub
    tasks and jobs have completed and aggregate any cached output of tasks
    for each job -- but job hierarchies are not rolled up.
    This can be replaced or specialized, for instance to do something with
    output from tasks incrementally or roll up information for job hierarchies.

    The lifecycle for a job is:

     - Setup partitioned set of work for tasks
     - Create a job task
     - Create sub tasks for each partition, added to job
     - Register all sub tasks AND job task for execution (e.g., put on queue)
     - Run and complete each sub task function
     - Call job task function (e.g., "job_done") until tasks complete
"""
from django.conf import settings

from .. import log
from ..utils.collections import accumulate_values
from . import Task
from . import send_queue_task
from .output import get_task_output
from .output import job_done


class Job( Task ):
    """
    A job is a cached SQS task that coordinates sub tasks:

      - Jobs must be used with cached sessions
      - They can cache read-only data shared with their sub tasks
      - Sub tasks can be added through job, or directly to tasks
      - Jobs can cache output of tasks and collate final result
      - A Job's 'task function' IS its 'done function'
    """

    def __init__( self, group, data=None, my_parent=None,
                    done_fn=job_done, **kwargs ):
        if my_parent:
            kwargs['my_cache'] = my_parent.cache_name

        # Data is a dict that will be pickled into the job session, and
        # then ADDED to task kwargs when each task function is called
        self.data = data or {}

        # The job is implemented a task; any kwargs are passed to the done_fn
        super().__init__( done_fn, group, my_job=my_parent, **kwargs )

        # Always add tasks to the same group
        self.group = group

        # List of cache_keys for looking up sub task sessions; this is only used
        # if the tasks are added with add_task
        self.task_keys = []

    def __str__( self ):
        return '{}JOB_{}'.format(
                    str(self.job) if self.job else '',
                    self.cache_key )

    def put_info( self ):
        """
        Async job done functions normally don't want the default task wrapper,
        as they don't want to finalize themselves if incomplete.
        """
        rv = super().put_info()
        rv.update({ 'async_task_wrapper': False })
        return rv

    def add_task( self, task_fn, **kwargs ):
        """
        Add a task to job and place task session in cache.
        Some options like priority will default to the job's settings,
        but can be overridden on a per-task basis.
        """
        kwargs['my_priority'] = kwargs.get( 'my_priority', self.priority )
        kwargs['expires'] = min( kwargs.get( 'expires', self.expires ),
                    self.expires )

        task = Task( task_fn, self.group, my_job=self,
                    my_cache=self.cache_name, **kwargs )

        self.cache_set( task.cache_key, task )
        self.task_keys.append( task.cache_key )
        return task

    def start( self ):
        """
        Once tasks are setup, add job task to cache so job data is available,
        and place tasks onto the message queue.
        Put ourselves on the queue last to process job done task.
        """
        self.cache_set( self.cache_key, self )

        for task_session in self.task_keys:
            task = self.cache.get( task_session )
            if task:
                log.info2("JOB queuing task: %s -> %s",
                                str(self), str(task))
                send_queue_task( task )
            else:
                log.warning_quiet("TASK NOT IN CACHE: %s", task_session)

        send_queue_task( self )

        log.info2("JOB queuing done, starting: %s", self)

    def process_output( self ):
        """
        Default functionality to complete job's output that returns accumulated
        rollup of any cached sub task output at the current point in time.
        Job specializations can override this behavior.
        """
        log.info("Processing job output: %s", self)
        output = None
        for task_session in self.task_keys:
            output = get_task_output( self.cache, task_session )
            output = accumulate_values( output, output )
        self.cleanup()
        return output

    def cleanup( self ):
        """
        Remove any remaining cache items related to the job
        """
        self.cache.delete_many( self.task_keys )
