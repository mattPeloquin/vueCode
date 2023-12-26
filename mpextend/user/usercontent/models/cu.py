#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ContentUser is the user proxy model for UserContent
"""
from django.db import models

from mpframework.common import log
from mpframework.common.events import sandbox_event
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.user.mpuser.models import mpUser
from mpframework.content.mpcontent.models import BaseItem
from mpextend.product.account.access import content_access_data

from .cu_manager import CuManager
from .user_item import UserItem
from .badge import Badge
from .user_badge import UserBadge


class ContentUser( SandboxModel ):
    """
    Bring together content and users
    Supports both data storage and logic for usage of content in the portal
    for each sandbox (if content is shared across sandboxes, usage in each is separate)
    """

    # Unlike AccountUser, staff-users DO have ContentUser records; since these are
    # per sandbox, the relationship to a staff user is M:1
    user = models.ForeignKey( mpUser, models.CASCADE, related_name='content_users' )

    # Records for each content tree/item used by user
    items = models.ManyToManyField( BaseItem, through=UserItem, blank=True )

    # Each badge in progress or earned by the user
    badges = models.ManyToManyField( Badge, through=UserBadge, blank=True )

    class Meta:
        unique_together = ( 'sandbox', 'user' )

    objects = CuManager()

    select_related = ( 'user' ,)
    select_related_admin = select_related

    lookup_fields = 'id__iexact', 'user__email__icontains'

    def __str__( self ):
        if self.dev_mode:
            return "cu({}){}".format( self.pk, self.user )
        return self.user.email

    def item_access_data( self, request, item, free, **kwargs ):
        """
        All authenticated user access requests run through this method
        to ensure the usage records are synched up with APAs.

        Returns launchable URL if the user has current rights to the item
        with the default APA.
        FUTURE - Support selection of APA if there are multiple options?

        If they can use, ensure user_item relationship exists.
        If not, return access data needed to put up selection dialog.
        """
        user = request.user
        assert self.user_id == user.pk
        log.debug("%s Start item access: %s -> %s", request.mptiming,
                    request.mpipname, item)
        if free:
            desc = u"Staff access" if user.access_staff_view else u"Free access"
            access_data = {
                'can_access': True,
                'apa_to_use': 0,
                'description': desc,
                }
        else:
            access_data = content_access_data( item, user )

        if access_data.get('can_access'):

            # The user content record may not get created if there is a
            # data error or other condition (like root user)
            cui = self.user_item( item )
            version = cui.item_version if cui else None
            access_data['progress_data'] = cui.progress_data if cui else None

            # For direct access, just send data for direct launch
            if kwargs.get('direct_access'):
                access_data.update({
                    'direct': item.access_data( request ),
                    })
            # Otherwise add access url; if item isn't ready, will be None
            else:
                access_url = item.get_access_url( request, version=version,
                                default_mode=access_data.get('default_mode'), **kwargs )
                if access_url:
                    # Access successful - as far as the server is concerned
                    access_data['access_url'] = access_url
                else:
                    log.warning("No access url: %s -> %s", request.mpipname, item)

            # Delegate updating information on this use (or attempted use)
            if cui and not user.is_root:
                cui.update_usage( access_data.get('apa_to_use'),
                                    kwargs.get('tree_id') )

        log.info2("ACCESS %s: %s -> %s",
                    'GRANTED' if access_data.get('can_access') else 'DENIED',
                    request.mpipname, item )
        log.info3("%s Access info %s: %s, %s", request.mptiming,
                    request.mpipname, item, access_data )
        return access_data

    @property
    def my_items( self ):
        """
        Return queryset for the user item MTM through table
        """
        return UserItem.objects.mpusing('read_replica')\
                .filter( cu=self )

    @property
    def my_items_full( self ):
        """
        Add select related info for my items
        """
        return self.my_items\
                .select_related('cu__user', 'item', 'top_tree__item', 'apa')

    def user_item( self, item ):
        """
        Given item or item id, return user_item for it
        If the item hasn't been associated with the user, setup a new
        content user relationship
        """
        if self.user.is_ready():
            return UserItem.objects.get_user_item( self, item, create=True )

    def start_item( self, item_id, progress_data='' ):
        ui = self.user_item( item_id )
        if ui:
            log.debug2("Saving item start: %s -> %s", self, ui)
            ui.set_progress( progress_data )

    def complete_item( self, item_id, progress_data=None ):
        """
        Assumes it is called from asynchronous update task.
        """
        ui = self.user_item( item_id )
        if ui:
            log.debug2("Completing item: %s -> %s", self, ui)
            ui.complete( progress_data )
            if ui.is_top_collection:
                sandbox_event( self.user, 'user_complete_collection', ui.item,
                                already_task=True )
            else:
                sandbox_event( self.user, 'user_complete_item', ui.item,
                                already_task=True )

    def update_item( self, item_id, progress_data ):
        ui = self.user_item( item_id )
        if ui:
            log.debug2("Saving progress data: %s -> %s", self, ui)
            ui.set_progress( progress_data )
