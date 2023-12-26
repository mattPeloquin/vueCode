#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF user authentication backend
"""
from django.conf import settings
from django.contrib.auth.backends import ModelBackend

from mpframework.common import log

from .models import mpUser


class mpUserBackend( ModelBackend ):
    """
    Extend Backend authentication to:
        1) Support mpUser case insensitive email as username
        2) Add sandbox to backend request for the user object
        3) Override the Django DB permissions framework (see has_perm below)
        4) Add SQL relationships and caching to the management of the user
           object in the request process. Goal is that references to request.user
           are optimized to leverage a distributed cached object that has
           pre-loaded most common info to avoid DB hits
    """

    def authenticate( self, _username=None, password=None, **kwargs ):
        """
        MPF ALWAYS needs pass a user for authentication,
        to handle tenancy.
        """
        user = kwargs.pop('user')
        log.debug2("mpUserBackend authenticate: %s", user)

        # For MPF configurations, the backend should never be asked to
        # authenticate a user with the username natural key
        if _username:
            raise Exception("ATTEMPT TO AUTHENTICATE MPUSER WITH USERNAME")

        if user and user.check_password( password ):
            log.debug2("User and password validated: %s", user)
            return user

    def get_user( self, id, sandbox=None ):
        """
        Get user by ID, overrides ModelBackend.get_user, used when
        getting user from sessions.

        MPF authentication overrides Django to pass along sandbox
        in normal authentication scenarios, allowing the sandbox
        to be set on the user object.
        """
        log.debug2("mpUserBackend get_user: %s -> %s", sandbox, id)

        # Django may call get user, for example during password confirm reset
        if not sandbox:
            if settings.MP_DEV_EXCEPTION:
                raise Exception("DJANGO get_user no sandbox")
            log.warning("NON-MPF get_user: %s", id)
            return mpUser.objects.get( id=id )

        # Get the user from the cache
        # Sandbox caching allows for users with multiple sandbox
        # privileges to be logged into more than one sandbox at a time
        return mpUser.objects.get_from_id( sandbox, id )

    def has_perm( self, user, perm, obj=None ):
        """
        Override DJ has_perm to for simplified Admin permissions scheme
        that DOES NOT USE AUTH permissions tables.

        DJ has a granular permissions scheme for admin privledges that uses
        hard-coded contenttype ids. MPF tenancy, features, and table structure
        doesn't work well with this scheme.
        DJ also overloads superuser to mean not only user management,
        but rights to all all actions on all tables; so has_perm is
        never called for a superuser.

        So to simplify life, DJANGO PERMSSIONS ARE DISABLED here
        """
        if user.access_staff:
            return True
