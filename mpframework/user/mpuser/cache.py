#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User cache support
    See user class overview for discussion of user caching
"""
from django.conf import settings

from mpframework.common.cache.timewin import timewin_start
from mpframework.common.cache.timewin import get_timewin_start
from mpframework.common.cache.timewin import get_timewin_hash


_timewin_timeout = settings.MP_CACHE_AGE['TIMEWIN_USER']


def user_timewin_start( request ):
    """
    Start a timewin and return the version key for the value
    """
    group = user_timewin_group( request )
    timewin_start( group, _timewin_timeout )
    return group

def user_timewin_get( request ):
    return get_timewin_start( user_timewin_group( request ) )

def user_timewin_hash( request ):
    return get_timewin_hash( user_timewin_group( request ) )

def user_timewin_group( request ):
    """
    Cache group version for user data based on a point in time
    """
    user = request.user
    return 'tw_user' + str(user.pk) + 's' + str(user.sandbox.pk)

def cache_group_user( id ):
    """
    Caching group based on user id, for user data only
    """
    return 'user' + str(id)

def cache_group_sandbox_user( user ):
    """
    Caching based on user and currently logged in sandbox
    """
    return 'sanduser' + str(user.sandbox.pk) + '_' + str(user.pk)
