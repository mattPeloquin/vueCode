#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tie plan to group account

    FUTURE - to use more than one plan with a user, the planuser proxy will need to implemented
"""
from django.db import models
from django.db import transaction
from django.db.utils import IntegrityError

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.user.mpuser.models import mpUser
from mpextend.product.account.models import GroupAccount

from . import BasePlan


class GroupPlanManager( TenantManager ):

    def get_or_create( self, ga ):
        assert ga
        log.debug2("get_or_create_groupplan: %s", ga)
        try:
            rv = self.get( group_account=ga )
        except self.model.DoesNotExist:
            log.info("Creating GroupPlan: %s", ga)
            try:
                with transaction.atomic():
                    rv = self.model( sandbox_id=ga.sandbox_id, group_account=ga )
                    rv.save()
            except IntegrityError:
                rv = self.get( group_account=ga )
        return rv


class GroupPlan( BasePlan ):
    """
    Plan that is tied to group accounts

    Allows GA admins to make plan templates that can be assigned to users
    Originally this capability was designed to support administering plans separate
    from group accounts, but since the vast majority of group plan business cases
    related to group account sponsors buying content for people, decided
    to simplify the plans to reflect that.
    """

    group_account = models.ForeignKey( GroupAccount, models.CASCADE,
                                       related_name='plans', db_constraint=False )

    # Users attached to this plan (should be subset of GA users)
    users = models.ManyToManyField( mpUser, related_name='plan_groups', blank=True )

    # Name for plan provided by GA admin
    _name = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, db_column='name' )

    objects = GroupPlanManager()

    select_related = ( 'group_account' ,)

    @property
    def name( self ):
        return self._name
