#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Core user model, which extends Django user
"""
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import BaseUserManager

from mpframework.common import log
from mpframework.common.events import sandbox_event
from mpframework.common.utils import now
from mpframework.common.cache import cache_rv
from mpframework.foundation.tenant.models.base.tenant_manager import TenantBaseManager

from .. import mpUserException
from ..cache import cache_group_user
from ..signals import mpuser_created


# The list of fields that can be passed to create_obj
CREATE_FIELDS = ['first_name', 'last_name', 'organization', 'title']


class mpUserManager( TenantBaseManager, BaseUserManager ):
    """
    Support optimizations and ease of use in frequent user access

    Username is managed as case insensitive email with tenancy decoration.
    Django by default treats username as case sensitive; MPF's
    mpUser backend overrides that by delegating to this manager for the lookup.
    The email is stored as the user originally typed it, but all subsequent
    requests for it are case-insensitive.
    """

    def get_by_natural_key( self, username ):
        raise mpUserException("MPUSER, NO NATURAL KEY")

    def get_from_id( self, sandbox, id ):
        """
        MAIN ACCESS POINT FOR LOADING USER OBJECTS FOR REQUESTS

        Gets user by ID with additional info and places in distributed cache.
        Used by the Auth Backend to get the user from session key and assign to the
        request object, which is where most user objects are accessed from.

        UNIT TEST code may call with a None sandbox, since the test code doesn't
        have a request context to define the sandbox.
        """
        try:
            user = self._get_from_id( id )

            # HACK TEST - Handle unit testing case, which sets sandbox later
            # to allow determining sandbox from from test user
            if sandbox is None:
                return user

            user.set_current_sandbox( sandbox )
            return user

        except self.model.DoesNotExist:
            if settings.DEBUG and not settings.MP_TESTING:
                raise
        log.warning("SUSPECT - Bad user/sandbox, id:%s sand: %s", id, sandbox)

    @cache_rv( keyfn=lambda _, id:( '', cache_group_user( id ) ) )
    def _get_from_id( self, id ):
        """
        Cache the user object to avoid DB hit on request load

        USER MAY BE LOGGED INTO MULTIPLE SANDBOXES and/or MULTIPLE SESSIONS, so
        no per-sandbox or per-session state should be cached here.
        """
        user = self.get( id=id )
        user._cache_extend()
        log.info2("Caching user get_from_id: %s", user)
        return user

    def get_user_from_email( self, email, sandbox ):
        """
        Returns user object for email if one exists for the sandbox, or None
        if they do not. Exceptions are thrown for data errors.

        Per-sandbox user emails tied to sandbox, so can duplicate across sandboxes.
        Provider users that sees_sandboxes only have one user/email for all sandboxes.
        Root users have access to all sandboxes, so there is only 1 of each root email.
        """
        log.detail3("get_user_from_email: %s -> %s", sandbox, email)
        provider = sandbox.provider
        rv = None

        # Use one DB operation to get all possible matches of provider/root
        q = Q( _provider=provider ) | Q( _provider=settings.MP_ROOT['PROVIDER_ID'] )
        users = self.filter( q, email__iexact=email )

        # More than 1 provider or root email returned from this query is a problem,
        # whereas could be many sandbox users with the same email, so track in loop
        first_pass = True
        for user in users:

            if user.is_root:
                log.warning("ROOT SPOOF: %s %s", email, sandbox )

            if user.sees_sandboxes:
                if first_pass:
                    rv = user
                    break
                raise mpUserException( "SUSPECT - MULTIPLE PROVIDER USERS: "
                            " %s, %s -> %s" % (email, sandbox, users))

            if user._sandbox_id == sandbox.id:
                log.debug2("Found user for sandbox: %s -> %s => %s", user, email, sandbox )
                rv = user
                break

            first_pass = False

        # Set current sandbox if found
        if rv:
            rv.set_current_sandbox( sandbox )

        return rv

    def limits_ok( self, **kwargs ):
        """
        Validate any policy limits
        """
        provider = kwargs['_provider']
        content_limit = provider.policy.get('site_limits.max_users')

        if content_limit:
            items = self.filter( _provider=provider ).count()
            if items >= content_limit:
                log.info("SUSPECT LIMIT: Attempt to exceed users: %s > %s",
                        provider, items)
                return False

        return True

    def create_obj( self, email, password, sandbox, create_info=None, **extra ):
        """
        Create a new sandbox user record.
        Users always start as non-staff that can only see one sandbox,
        and can be promoted after creation.
        create_info is information that may be provided and passed along
        to other applications.
        """
        if not email and not sandbox:
            raise ValueError("Email and sandbox and must be provided")
        if not self.limits_ok( _provider=sandbox.provider ):
            return

        email = self.normalize_email( email )
        extra_fields = { 'hist_created': now() }

        # Setup name based on info provided
        # If non-blank is not provided for first or last, use part of email
        name_parts = email.split('@', 2)[0].split('.', 2)
        first_name = extra.pop('first_name', '')
        if not first_name: first_name = str(name_parts[0]).capitalize()
        last_name = extra.pop('last_name', '')
        if not last_name: last_name = str(
                    name_parts[1] if len(name_parts) > 1 else '').capitalize()

        # Add extra initial info
        extra_fields.update({
            'first_name': first_name,
            'last_name': last_name,
            })

        # If user terms acceptance is on, add to record
        if not sandbox.options['user.force_accept_terms']:
            acceptance_text = u"Accept On Create: {}-{}".format( email, now() )
            log.debug("Saving user acceptance info: %s", acceptance_text)
            extra_fields.update({ 'init_terms': acceptance_text })

        # Now add/update terms handed to create_obj that are valid
        # Users can create custom login forms, which will pass along values, which
        # is why this needs to be scrubbed here
        extra_fields.update({ k: v for k, v in extra.items() if k in CREATE_FIELDS })

        log.info2("Creating new user: %s -> %s", sandbox, email)
        user = self.model( _provider=sandbox.provider, _sandbox=sandbox,
                    email=email, **extra_fields )
        user.set_password( password )

        # Create user DB record and use health and signals and on dependent
        # apps to complete the initialization
        user.save( using=self._db )
        mpuser_created.send( sender=self.__class__, user=user, create_info=create_info )
        user.health_check( sandbox, create_info )

        log.info("CREATE USER: %s -> %s", sandbox, user)
        sandbox_event( user, 'user_signup', sandbox)
        return user

    def lookup_queryset( self, sandbox ):
        """
        Override base because sandbox field has different name
        """
        return self.filter( _sandbox=sandbox )
