#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF Bots

    Bots are self-perpetuating Tasks for ongoing asynchronous work
    without dedicated processes/threads and without a master.

    Bot work is done in Task functions. Bots "live" by creating new Tasks
    after finishing their current one. State for the Bot is maintained
    in the Task session cache.

    When a spooler (or dev) process starts, it starts any registered Bots.
    If Bot's name key is not in the cache, there is a race to register it.
    Bots can run perpetually or start/stop based on criteria or admin requests.

    Bot work is interleaved with other task work, and can be structured
    with priority levels and server configuration.

    MPF uses SQS FIFO MessageGroups to limit each Task to active execution
    of one message at a time. This is desired for most bots since it
    provides natural throttling for work that is not time-critical.

    Helpers for Bots are defined here; most Bot functionality is
    provided by the Task framework, and specifics of bot activity is
    defined in the Tasks for specific bots.
"""
from django.core.cache import caches

from .. import log
from ..utils import get_random_key
from . import Task
from . import send_queue_task

cache = caches['session']
_BOTS = set()

DEFAULT_BOT_PRIORITY = 'LS'


class Bot():
    """
    Static base class for Bots, provides convenient singleton wrapper for
    the Bot primitives and support for registration.
    """
    NAME = '_BOT_NAME_'     # Unique cache and Task MessageGroup
    FN = None               # Set to mp_async Task function
    PRIORITY = DEFAULT_BOT_PRIORITY
    INITIAL_STATE = {}

    @classmethod
    def register( cls ):
        _BOTS.add( cls )

    @classmethod
    def start( cls ):
        return bot_start( cls.NAME, cls.FN, cls.INITIAL_STATE,
                    cls.PRIORITY )

    @classmethod
    def state( cls, **kwargs ):
        return bot_state( cls.NAME, **kwargs )

    @classmethod
    def next( cls, state, **kwargs ):
        kwargs['bot_priority'] = kwargs.get( 'bot_priority', cls.PRIORITY )
        return bot_next( cls.NAME, cls.FN, state, **kwargs )

    @classmethod
    def stop( cls ):
        bot_stop( cls.NAME )

def start_bots():
    """
    Called by every server process on start. May also be used to
    restart stopped bots.
    """
    log.info("BOTS STARTING")
    for bot in _BOTS:
        bot.start()

def stop_bots():
    """
    Provide admin control to suspend bot execution.
    """
    log.info("BOTS STOPPING")
    for bot in _BOTS:
        bot.stop()

# Bot primitives

def bot_start( name, fn, state, priority=DEFAULT_BOT_PRIORITY ):
    """
    Start bot by kicking off first task if not already going.
    """
    new_key = name + get_random_key()
    bot_key = cache.get_or_set( name, new_key )
    if bot_key == new_key:
        log.info("BOT START: %s -> %s", name, state)
        return bot_next( name, fn, state, bot_key=bot_key,
                    bot_priority=priority )

def bot_state( name, **kwargs ):
    """
    If the bot still matches key, return the given state.
    """
    bot_key = cache.get( name )
    if bot_key == kwargs['bot_key']:
        return kwargs['bot_state']
    log.info("BOT %s will not continue", name)

def bot_next( name, fn, state, **kwargs ):
    """
    Create a new Task to perpetuate the Bot.
    """
    priority = kwargs.get( 'bot_priority', DEFAULT_BOT_PRIORITY )
    task = Task( fn, name, bot_key=kwargs['bot_key'],
                bot_state=state, my_priority=priority )
    send_queue_task( task )
    log.debug("BOT TASK: %s -> %s", name, state)
    return task

def bot_stop( name ):
    """
    Start a bot if not already going.
    """
    cache.delete( name )
    log.info("BOT %s is stopping", name)
