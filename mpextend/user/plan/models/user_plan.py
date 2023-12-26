#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Direct link of user to one plan

    FUTURE - change UserPlan to 1:M relationship to plans rather then concrete inheritance
"""
from django.db import models
from django.db import transaction
from django.db.utils import IntegrityError

from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.user.mpuser.models import mpUser

from . import BasePlan


def _user_plan_keyfn( _, user ):
    """
    Cache user plans without group version keys, based on user/sandbox
    """
    return 'userplan-' + user.cache_group, ''


class UserPlanManager( TenantManager ):

    def get_or_create( self, user ):
        if not user.is_ready():
            return
        log.debug2("UserPlan get_or_create: %s", user)
        try:
            rv = self.get( sandbox=user.sandbox, _user=user )
        except self.model.DoesNotExist:
            log.debug("Creating UserPlan: %s", user)
            try:
                with transaction.atomic():
                    rv = self.model( sandbox=user.sandbox, _user=user )
                    rv.save()
            except IntegrityError:
                rv = self.get( sandbox=user.sandbox, _user=user )
        return rv

    @cache_rv( keyfn=_user_plan_keyfn, keyname='' )
    def get_plans( self, user ):
        """
        Cache plans for the given user
        FUTURE - support multiple plans
        """
        log.debug("Loading plans: %s", user)
        rv = ()
        user_plan = self.get_or_create( user )
        if user_plan:
            rv += ( user_plan ,)
        return rv


class UserPlan( BasePlan ):
    """
    A plan that is tied to a specific user, which is the user's default plan
    """
    _user = models.ForeignKey( mpUser, models.CASCADE,
                               blank=True, null=True, related_name='plan_user',
                               db_column='user_id' )

    objects = UserPlanManager()

    @property
    def user( self ):
        """
        Fixup use of user references to set current sandbox to plan's sandbox
        if plan for staff user referenced outside request.
        """
        self._user.sandbox_id = self.sandbox.pk
        return self._user

    @property
    def name( self ):
        return u"{} default plan".format( self.user.username )

    def add_collections( self, trees ):
        """
        Add top-level collections to plan
        """
        log.debug("Adding trees to plan: %s -> %s", self, trees)
        self.add_tree( self.user, trees )
