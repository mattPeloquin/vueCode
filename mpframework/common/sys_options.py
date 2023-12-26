#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    System Global options

    System global options are stored in the root sandbox's
    policy YamlField. These track system-wide options such
    as logging settings and certain throttling and polling.

    Option defaults can be specified in config settings, but
    they will not be overridden after process load if values
    already exists in the DB.
    Option reads are cached in default cache, with invalidation
    controlled by the caller.

    Options use MP_PLAYPEN_OPTIONS namespace. By default
    DEV SERVER OPTIONS ARE SEPARATE FROM PRODUCTION SERVERS.
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.logging.settings import log_setting_initial_values
from mpframework.common.cache import cache_rv
from mpframework.common.cache.groups import cache_group_system
from mpframework.common.cache.groups import invalidate_group_system


@cache_rv( keyfn=lambda:( 'root_sandbox',
            cache_group_system( namespace='options' ) ) )
def root():
    """
    Return cached root sandbox instance
    """
    from mpframework.foundation.tenant.models import Sandbox
    return Sandbox.objects.get( id=1 )

def update_options( opts ):
    """
    For each key-value in the opts dict, set an option
    if it exists, and then save and invalidate.
    """
    root_sandbox = root()
    for key, value in opts.items():
        setter = globals().get( key )
        if setter:
            setter( value, root=root_sandbox )
    root_sandbox.save()

def invalidate_all():
    invalidate_group_system('options')

def init_option_accessors( context, options ):
    """
    For each of a set of given options, create a closure
    for the given context for getting/setting their value.
    """
    for option in options:
        log.detail3("Adding global option accessor: %s", option)

        def wrapper( value=None, name=option[0], default=option[1],
                        invalidate=False, root=None ):
            # Can be used stand-alone or in bulk updates
            # Caller can explicitly request invalidation for reads
            if invalidate:
                invalidate_all()
            if value is None:
                return _get_option( name, default )
            else:
                return _put_option( root, name, value )

        context[ option[0] ] = wrapper

# Initialize options on module load, so they are available immediately
# They may be overridden later
init_option_accessors( globals(),
            settings.MP_OPTIONS + log_setting_initial_values() )

# Implement seperation of servers by playpen
def _fixup( name ):
    return '%s_%s' % ( settings.MP_PLAYPEN_OPTIONS, name )

@cache_rv( keyfn=lambda name, _:( _fixup(name),
            cache_group_system( namespace='options' ) ),
            buffered='local_medium' )
def _get_option( name, default ):
    """
    For caching option access assume names are unique; args are not needed.
    """
    name = _fixup( name )
    rv = root().policy.get( name, default=default )
    log.debug("Global option get %s: %s", name, rv)
    return rv

def _put_option( root_sandbox, name, value ):
    """
    Support individual and bulk updates
    """
    save = not root_sandbox
    root_sandbox = root_sandbox or root()
    name = _fixup( name )
    log.info2("Global option set %s: %s", name, value)
    root_sandbox._policy.set( name, value )
    if save:
        root_sandbox.save()
