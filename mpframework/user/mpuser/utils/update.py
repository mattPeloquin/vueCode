#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support updating selected user fields if the user goes through
    either the create user or the login screen.
"""

from mpframework.common import log
from mpframework.common.utils.request import QUERYSTRING_PREFIX


def user_request_update( request ):
    """
    Update user based on update querystrings.
    """
    user = request.user

    # DB is only updated if user authenticates
    if not ( user and user.is_authenticated ):
        return

    # Save any update values from querystrings
    values = user_request_querystrings( request, remove=True )
    if values:
        log.info("Updating user: %s -> %s", user, values)
        for name, value in values.items():
            if name not in _SKIP_SAVE:
                setattr( user, name, value )
        user.save()

def user_request_querystrings( request, remove=False ):
    """
    Remove set of well known querystring names from request and
    return values in dict with user model field names.
    HACK - May update user on a get in the case of a redirect,
    but even when a POST is made on login, querystings in GET.
    """
    rv = {}
    new_qs = request.GET.copy()
    for qsn, field in _QS_FIELDS:
        qsn = QUERYSTRING_PREFIX + qsn
        qv = new_qs.get( qsn )
        if qv:
            rv[ field ] = qv
            new_qs.pop( qsn )
    if remove:
        request.GET = new_qs
    return rv

# Explicit list of fields willing to change
# Make sure these don't compromise security and that querystring
# namespace doesn't overlap with other areas
_SKIP_SAVE = [ 'email' ]
_QS_FIELDS = [
    ( 'email', 'email' ),
    ( 'fname', 'first_name' ),
    ( 'lname', 'last_name' ),
    ( 'org', 'organization' ),
    ( 'title', 'title' ),
    ( 'key', 'external_key' ),
    ( 'group', 'external_group' ),
    ( 'tag', 'external_tag' ),
    ( 'tag2', 'external_tag2' ),
    ( 'tag3', 'external_tag3' ),
    ( 'postal', 'postal_code' ),
    ( 'country', 'country' ),
    ]
