#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF Task - queable function calls

    Tasks are the smallest unit of task work, usually scheduled
    on a distributed task queue.
    Tasks can be stand-alone or built into job hierarchies.
"""
from django.conf import settings
from django.core.cache import caches
from django.db import connections
from django.db import close_old_connections
from django.db.utils import OperationalError

from .. import log
from ..cache import stash_method_rv
from ..deploy import load_module_attr
from ..utils import now
from ..utils import timedelta_future
from ..utils import timedelta_seconds
from ..utils import get_random_key
from . import get_module_name
from .output import task_output_key
from .mp_async import is_async_fn
from .mp_async import run_routine_async
from .mp_async import mp_async


TASK_CACHE_PREFIX = 'task'
DEFAULT_MAX_MINUTES = 60  # 1 hour; ongoing jobs will renew themselves


@mp_async
def async_task_wrapper( retry=True, **kwargs ):
    """
    Standardized error handling for asynchronous task function execution
    """
    task = kwargs['my_task']
    output = "TASK EMPTY"
    try:
        fn = kwargs.pop('my_task_fn')
        log.debug2("Executing wrapped task fn: %s, retry %s", fn, retry)
        try:
            output = fn( **kwargs )

        except OperationalError as e:
            # Connections can be closed on tasks; do one retry to reopen
            if retry:
                log.info("TASK ASYNC DB conn retry: %s -> %s", fn, e)
                connections.close_all()
                kwargs['my_task_fn'] = fn
                async_task_wrapper( False, **kwargs )

    except Exception as e:
        if settings.MP_TESTING:
            raise
        log.exception("TASK ASYNC: %s", task)
        output = "Task exception: %s" % e

    if task.cache:
        return task.finalize( output )


class Task:
    """
    Tasks represent the information needed to call a "task function".
    This encapsulates knowledge about pickling and executing, but
    message queue and task processing mechanics should not be here.

    Task work is done by a task function passed to the constructor.
    These functions have some restrictions:
     - Must use an @mp_async decorater
     - Can only use kwargs (implicit or explicit)
     - Must accept **kwargs as they may be passed special keys
     - Cannot use the following kwarg keys:
            'my_task', 'my_task_fn', 'my_priority', 'my_cache', 'my_job'
    """
    DEFAULT_PRIORITY = 'MS'
    HIGH_SPOOL = ['HS']

    # Tasks are partitioned into SQS MessageGroups within each priority queue.
    # For normal priorities, only one Task per group is processed at a time,
    # usually based on tenancy, to ensure distribution of processing.
    # The Task group also optionally limits what groups a server will process,
    # based on prefixes in the TASK_GROUPS setting.
    # Group used if no group is specified.
    DEFAULT_GROUP = 'DEFAULT'
    # Name for default setting of servers processing all Task groups.
    ALL_GROUP = 'TASK_ALL'

    class TaskPlaceholder:
        """
        Used for non-cached tasks to create a pickled my_task object
        """
        cache = None
        def __init__( self, fn_name, kwargs ):
            self.handler_name = fn_name
            self.kwargs = kwargs
            self.priority = self.kwargs.pop( 'my_priority', Task.DEFAULT_PRIORITY )
        def __str__( self ):
            return 'nocache{}_{}'.format( self.priority, self.handler_name )

    def __init__( self, fn, group, **kwargs ):
        """
        Setup the information necessary to execute a task:
            fn -is the task function that will execute asynchronously
            group - the message group as described below; only
            one Task at a time is processed from a message group.
            Use a random string to force completely separate
            execution of a Task as soon as possible.
        """
        self.priority = kwargs.pop( 'my_priority', self.DEFAULT_PRIORITY )
        my_job = kwargs.pop( 'my_job', None )

        # Package remaining kwargs AS DICT into a task session
        # This will be pickled into session or posted on SQS, and handed
        # to task function when executed.
        self.kwargs = kwargs

        # Queue MessageGroup, which controls visibility of inflight messages --
        # only one message from a group is processed at a time.
        # Group prefixes also determine whether a server processes the task.
        # If group is object with a unique_key it given the default prefix and
        # grouped by that key. Custom strings define their own prefixes, while
        # no group is added to a shared system group.
        if not group:
            group_key = 'SYSTEM'
        else:
            group_key = getattr( group, 'unique_key', None )
        if group_key:
            group = '{}_{}'.format( self.DEFAULT_GROUP, group_key )
        self.message_group = group

        # Most tasks and all jobs are cached, so info to reconsitute the task
        # will be stored as a session in the cache
        my_cache = kwargs.get( 'my_cache', 'session' )
        if my_job and not my_cache:
            raise Exception("Job Tasks must use cached sessions")
        self.cache_name = my_cache
        self.key = get_random_key( prefix='t' )

        # Full module NAME of function to handle task
        self.handler_name = fn if isinstance( fn, str ) else get_module_name( fn )

        # For cached tasks, manage expiration of both task execution and cache life.
        # Note that for cache resources, a simple max is used with expire_seconds
        # vs. calculating window each time somethign is cached.
        self.created = now()
        self.expired = False
        self.expires = self.kwargs.get( 'expires',
                                   timedelta_future( minutes=DEFAULT_MAX_MINUTES ) )
        self.expire_seconds = timedelta_seconds( self.expires - self.created )

        # For cached tasks that are part of job, don't store the entire job,
        # so copies won't be pickled for every task
        self.job_cache_info = my_job.cache_info if my_job else {}

        log.debug2("Created %s: %s", self.__class__.__name__, self)

    def __str__( self ):
        name = self.cache_key if self.cache else ''
        return '{}{}-{}_{}'.format( name, self.priority, self.message_group,
                                        self.handler_name )

    @property
    @stash_method_rv
    def job( self ):
        """
        Load job for task from cache -- Jobs CAN ONLY USE CACHED tasks
        """
        assert( self.cache )
        jci = self.job_cache_info
        if jci:
            rv = caches[ jci['cache_name'] ].get( jci['task_key'] )
            log.debug("Loaded task parent job from cache: %s", rv)
            return rv

    @property
    def cache( self ):
        if self.cache_name:
            return caches[ self.cache_name ]

    def put_info( self ):
        """
        Returns the information needed to execute the task, which will either
        be the information itself, or the info access cached task session
        """
        if self.cache:
            self.cache_set( self.cache_key, self )
            return { 'cached_task': self.cache_info }
        else:
            return self.kwargs

    def finalize( self, output ):
        """
        Place output from a task function into cache for future use by
        get_task_output or custom job completion, and indicate
        the task processing is done by removing session from cache.
        """
        if self.cache:
            log.debug("Finalizing: %s", self)
            self.cache_set( task_output_key( self.cache_key ), output )
            self.cache.delete( self.cache_key )

    def cache_set( self, key, value ):
        expire_seconds = getattr( self, 'expire_seconds', self.cache.default_timeout )
        log.cache("CACHE SET TASK: %s -> %s", key, value)
        self.cache.set( key, value, expire_seconds )

    @property
    @stash_method_rv
    def cache_key( self ):
        if self.cache:
            if self.job_cache_info:
                prefix = self.job_cache_info['task_key']
            else:
                prefix = TASK_CACHE_PREFIX
            return '{}_{}'.format( prefix, self.key )
        else:
            return ''

    @property
    def cache_info( self ):
        if self.cache:
            return {
                'cache_name': self.cache_name,
                'task_key': self.cache_key,
                }
        else:
            return {}

    @classmethod
    def execute( cls, fn_name, payload=None ):
        """
        Given fn_name and payload kwargs AS DICT, execute the task fn.
        Any job.data is injected AND WILL OVERWRITE kwargs with same keys.
        Tasks that are part of jobs MUST be cached.
        Returns True if task was handled asynchronously.
        """
        # Task functions must be mp_async and importable from module
        fn = load_module_attr( fn_name )
        if not fn:
            raise Exception("TASK cannot find: {}".format( fn_name ))
        if not is_async_fn( fn ):
            raise Exception("TASK function not @mp_async: {}".format( fn_name ))

        # Manage items passed in kwargs
        payload = payload or {}
        cached = payload.get( 'cached_task', {} )
        immediate = payload.get( 'immediate_task', False )
        message = payload.pop( 'async_message', None )
        try:
            if cached:
                cache = caches[ cached['cache_name'] ]
                key = cached['task_key']
                task = cache.get( key )
                log.cache("CACHE GET TASK: %s -> %s", key, task)

                # If cached info for task has expired, nothing to do but bail
                if not task or getattr( task, 'expired', False ):
                    log.warning("{} EXPIRED, skipping execution".format( key ))
                    cache.delete( key )
                    return

                # Load the kwargs for task fn and add task object
                kwargs = task.kwargs
                kwargs['my_task'] = task
            else:
                kwargs = payload
                kwargs['my_task'] = cls.TaskPlaceholder( fn_name, payload )

            # Bypass spooler file queues and do immediate synchronous execution.
            # Use CAREFULLY to run small tasks, preferably with no DB access.
            # Tasks run here will not count towards spooler max tasks.
            if immediate:
                log.debug_on and log.debug("TASK IMMEDIATE: %s -> %s",
                            fn_name, str(kwargs)[:256])

                fn( **kwargs )

                close_old_connections()
                return

            # Otherwise call task function async via spooler mechanism
            log.debug_on and log.debug("TASK SPOOL: %s -> %s",
                        fn_name, str(kwargs)[:256])
            # Add spooler call info
            if message:
                kwargs['async_message'] = message
            if kwargs['my_task'].priority in cls.HIGH_SPOOL:
                kwargs['spool_priority'] = 1
            # Normally task calls are wrapped in standard error handling
            wrapper = payload.get( 'async_task_wrapper', async_task_wrapper )
            if wrapper:
                kwargs['my_task_fn'] = fn
                fn = wrapper

            run_routine_async( fn, **kwargs )

            return True

        except Exception as e:
            extra_log = ""
            if cached:
                extra_log = "%s" % cached
                cache = caches[ cached.get('cache_name') ]
                if cache:
                    # Create error marker in cache and remove key to prevent
                    # the same error from happening again
                    task = cache.get( cached['task_key'] )
                    cache.set( 'ERROR_LOG_{}'.format( cached['task_key'] ), task )
                    cache.delete( cached['task_key'] )
                    extra_log += " -> %s" % task
            log.exception("TASK %s -> %s %s", fn_name, payload, extra_log,
                        logger='mp.direct_mail')
            connections.close_all()
            raise
