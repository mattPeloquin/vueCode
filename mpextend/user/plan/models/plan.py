#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plans are user/staff/provider groupings of content.

    Unlike content usage which is tracked, plans are ephemeral.
    Plans do not capture state or content use. Thus plans can be
    shared for purposes such as a team manager setting
    up a curriculum for their team members to complete.

    FUTURE - plans are only implemented for top-level collections, but
    could be expanded to sub-collections and individual items
"""
from mpframework.common import log
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.model.concrete_mixin import ConcreteBaseMixin
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.models import Tree


# HACK FUTURE - invalidate user directly since request user with staff sandbox
# is available here
def _hack_invalidate( user ):
    from mpframework.common.cache import invalidate_key
    from .user_plan import _user_plan_keyfn
    invalidate_key( _user_plan_keyfn( None, user )[0] )


class BasePlan( CachedModelMixin, ConcreteBaseMixin, SandboxModel ):
    """
    Plan Concrete Base

    Defines core plan behavior and used for links to plans.
    Specializations define how the plan is connected to users.

    Each collection connected to a plan includes everything in node and sub-nodes.
    """

    # A dict with information on item ids included in the plan
    # DB integrity is not used; plans heal by removing invalid items
    content = YamlField( null=True, blank=True )

    objects = TenantManager()

    def __str__( self ):
        if self.dev_mode:
            return "p({},s:{}){}".format( self.pk, self.sandbox_id, self.name )
        return self.name

    @property
    def name( self ):
        # Base plans should never be visible in the UI
        return "BasePlan({})".format( self.pk )

    @property
    def top_ids( self ):
        """
        Returns all top-level collection ids
        """
        rv = self.content['top_ids']
        return rv if rv else []


    @property
    def all_items( self ):
        """
        Returns all items associated with the plan
        FUTURE - expensive DB operation, may not be needed outside testing
        """
        rv = set()
        for top_id in self.top_ids:
            top = Tree.objects.get_quiet( id=top_id, sandbox=self.sandbox )
            if top and top.is_top:
                rv.update( top.all_items() )
        return rv

    #--------------------------------------------------------------------
    # API calls can use object or ids

    def add_tree( self, user, tops ):
        """
        Can take baseitem or id of tree, or list of either
        Doesn't verify the item is actually a tree; bad ids will be ignored
        when read
        """
        log.debug2("Plan adding root tree: %s -> %s", self, tops)
        new_ids = []
        if not isinstance( tops, list ):
            tops = [ tops ]

        for top in tops:
            new_id = None
            try:
                if isinstance( top, Tree ):
                    new_id = top.pk
                else:
                    new_id = int( top )

            except Exception as e:
                log.error_quiet("Bad value passed to add_tree: %s -> %s", top, e)

            if new_id:
                new_ids.append( new_id )

        if new_ids:
            new_ids.extend( self.content.get( 'top_ids', [] ) )
            new_ids = list( set( new_ids ) )
            self.content['top_ids'] = new_ids
            self.save()
            _hack_invalidate( user )

    def remove_tree( self, user, tree ):
        log.debug("Plan removing tree: %s, %s: %s", self, tree, self.content)
        if isinstance( tree, Tree ):
            tree = tree.pk
        tree = int( tree )
        if self.content['top_ids']:
            try:
                self.content['top_ids'].remove( tree )
                self.save()
                _hack_invalidate( user )

            except ValueError as e:
                log.info2("SUSPECT - Failed remove tree from plan: %s, %s -> %s",
                            user, tree, e)
