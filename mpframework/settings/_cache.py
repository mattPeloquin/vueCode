#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cache settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py

    See mpframework/common/cache for discussion of MPF
    performance caching, versioning, and invalidation designs.
"""

from mpframework.common.deploy.paths import work_path

from . import env


"""--------------------------------------------------------------------
    Redis, local buffer, and dev cache configuration

    Setup Django caches to use either remote or local caches,
    depending on the configuration options.

    Django caches separate operational caches with namespace prefixes
    (and potentially logical/physical caches). The prefixes allow items
    to be mixed in local buffers while potentially being separated across
    distributed caches.
    Caches sensitive to code changes (e.g., templates, model data,etc.)
    INCLUDE CODE VERSION IN KEY NAMESPACE. In other caches, if an
    incompatibility is introduced the cache needs to be cleared manually
    or the items invalidated by versioning the key name.
    Prefixes also take into account profile playpens for seperation
    of production from debug and can aid in debugging cache content.
"""

_shared = {
    # Override Django key making behavior to support MPF schemes
    'KEY_FUNCTION': 'mpframework.common.cache.key.key_function',
    'VERSION': '',
    }

def _cache_options( location=None ):
    """
    Shared values for setting up cache locations.
    In local dev/test, all caches share key namespace, while in production
    different caches otherwise.
    """
    rv = _shared.copy()
    _location = ''
    if env.MP_CLOUD:
        # Setup to use redis Elasticache
        _backend = 'mpframework.common.cache.redis.mpRedisCache'
        _location = location
        _options = {
            'IGNORE_EXCEPTIONS': False,
            }
    else:
        """
        Dev Local memory cache
        Bump the max entries up from Django 300 default and set culling to
        clear entire cache (instead of default random cull based on modulo).
        This is for testing speed and to ensure items expected in session
        cache like work tasks aren't purged.
        """
        _backend = 'mpframework.common.cache.locmem.mpLocMemCache'
        _options = {
            'CULL_FREQUENCY': 0,
            'MAX_ENTRIES': 16000,
            }
    rv.update({
        'LOCATION': _location,
        'BACKEND': _backend,
        'OPTIONS': _options,
        })
    return rv

"""--------------------------------------------------------------------
    Performance caching
    Intermediate data results for acceleration and lowering server load.
"""

# Version cache, supports chained invalidation of version groups
_version = _cache_options( env.MP_ROOT_CACHE['VERSION'] )
_version.update({
    # Versioning shares information across code versions, since invalidation
    # signals need to be available to all servers.
    'KEY_PREFIX': 'ver:{}'.format( env.MP_PLAYPEN_CACHE ),
    'TIMEOUT': env.MP_CACHE_AGE['VERSION'],
    })

# Main temporary performance cache with versioning
_default = _cache_options( env.MP_ROOT_CACHE['DEFAULT'] )
_default.update({
    'KEY_PREFIX': '{}{}'.format( env.MP_PLAYPEN_CACHE, env.MP_CODE_CURRENT ),
    'TIMEOUT': env.MP_CACHE_AGE['DEFAULT'],
    })

# Template caching separate for easier management
_template = _cache_options( env.MP_ROOT_CACHE['TEMPLATE'] )
_template.update({
    'KEY_PREFIX': '{}{}'.format( env.MP_PLAYPEN_CACHE, env.MP_CODE_CURRENT ),
    'TIMEOUT': env.MP_CACHE_AGE['TEMPLATE'],
    })

# Persisting performance separate, not tied to code version
_persist = _cache_options( env.MP_ROOT_CACHE['PERSIST'] )
_persist.update({
    'KEY_PREFIX': 'per:{}'.format( env.MP_PLAYPEN_CACHE ),
    'TIMEOUT': env.MP_CACHE_AGE['PERSIST'],
    })

"""--------------------------------------------------------------------
    Session caches
    Information that is temporary but important to continuity
    (can't blow away without affecting current user/system state).
    This includes user, access, IP tracking, job/task, etc. sessions.
"""

# Django user sessions
_user_session = _cache_options( env.MP_ROOT_CACHE['USER'] )
if env.MP_WSGI:
    _user_session.update({
        'KEY_PREFIX': '{}'.format( env.MP_PLAYPEN_CACHE_USER ),
        'TIMEOUT': env.MP_CACHE_AGE['USER'],
        })
elif env.MP_IS_DJ_SERVER:
    # If running dev app, use file based session cache so don't have to log in
    # every time and dev server restarted - ALSO NEEDED FOR SOME TEST CASES
    _user_session = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': work_path( env.MP_PLAYPEN_CACHE, 'session_cache' ),
        }

# Session blackboard
_session = _cache_options( env.MP_ROOT_CACHE['SESSION'] )
_session.update({
    'KEY_PREFIX': 'ses:{}'.format( env.MP_PLAYPEN_CACHE ),
    'TIMEOUT': env.MP_CACHE_AGE['SESSION'],
    })

# Information tracked for requests
_request = _cache_options( env.MP_ROOT_CACHE['REQUEST'] )
_request.update({
    'KEY_PREFIX': 'req:{}'.format( env.MP_PLAYPEN_CACHE ),
    'TIMEOUT': env.MP_CACHE_AGE['REQUEST'],
    })

"""--------------------------------------------------------------------
    Local Server cache and buffer

    These caches are shared across processes on a SINGLE SERVER
    The default use is for implementing temporary local buffering
    of frequently hit items stored in distributed cache.

    The small, med, and large refer to the size of data stored,
    and provide tuning for memory use related to size and expected
    number of items in the caches. Which one is used is defined
    in code, based on expected profile.
"""
_local_small = _cache_options()
_local_medium = _cache_options()
_local_large = _cache_options()

if env.MP_WSGI:
    _local_backend = 'mpframework.common.cache._uwsgi.UwsgiCache'
    _local_small['LOCATION'] = 'local_small'
    _local_medium['LOCATION'] = 'local_medium'
    _local_large['LOCATION'] = 'local_large'
else:
    _local_backend = 'django.core.cache.backends.locmem.LocMemCache'
    _local_small.update({ 'KEY_PREFIX': 'ls' })
    _local_medium.update({ 'KEY_PREFIX': 'lm' })
    _local_large.update({ 'KEY_PREFIX': 'll' })

_local_shared = {
    'BACKEND': _local_backend,
    }
_local_small.update( _local_shared )
_local_medium.update( _local_shared )
_local_large.update( _local_shared )

_local_small['TIMEOUT'] = env.MP_CACHE_AGE['BUFFER_SMALL']

#---------------------------------------------------

CACHES = {
    # Local server buffer caches
    'local_small': _local_small,
    'local_medium': _local_medium,
    'local_large': _local_large,

    # Chained version lookup
    'version': _version,

    # General performance caching
    'default': _default,    # Name needed by Django as default cache
    'persist': _persist,    # Long life/no group invalidate performance

    # Template performance caching
    'template': _template,
    'template_fragments': _template, # Django well-known name

    # Long-term state caching
    'users': _user_session, # Django's SESSION_CACHE_ALIAS
    'session': _session,    # User tasks, access sessions, bots, etc.
    'request': _request,    # Request tracking, throttling
    }
