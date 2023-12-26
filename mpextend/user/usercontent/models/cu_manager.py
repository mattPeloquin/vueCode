#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manager for ContentUser
"""
from django.db import transaction
from django.db.utils import IntegrityError

from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.foundation.tenant.models.base import TenantManager


class CuManager( TenantManager ):

    def get_contentuser( self, user, create=True ):
        """
        Get or create ContentUser for mpUser and CURRENT user sandbox.
        Returns None if UserContent can't be created due to expected reasons,
        raises an exception if there is a problem.
        """
        if user and user.is_authenticated:
            return self._get_from_user( user, create )
        else:
            log.debug("Attempt to create visitor ContentUser: %s", user)

    @cache_rv( keyfn=lambda _s, user, _c:( '', user.cache_group ) )
    def _get_from_user( self, user, create ):
        """
        Cache the ContentUser (and attached user) object for the current
        user sandbox (staff users can have more than one ContentUser).
        Tie caching of content user to the user invalidation group since
        the cu selects related user data.
        """
        sandbox = user.sandbox
        try:
            log.debug("Getting ContentUser: %s -> %s", sandbox, user)

            return self.get( sandbox_id=sandbox.pk, user_id=user.pk  )

        except self.model.DoesNotExist:
            if not create:
                return

        # There should be only one contentuser, but due to lazy record
        # creation race conditions can occur.
        try:
            with transaction.atomic():
                log.info("HEAL - Creating ContentUser: %s -> %s", sandbox, user)
                user.clear_stash()

                cu = self.model( sandbox=sandbox, user=user )
                cu.save()

                # Make the user object refresh to see the CU
                user.save()

                return cu

        except IntegrityError as e:
            # FUTURE - if conflicts happen often, reduce creation contention
            log.info2("RACE creating content user: %s, %s -> %s",
                        sandbox, user, e)
            # Return the object that was just created
            return self.get( sandbox_id=sandbox.pk, user_id=user.pk )
