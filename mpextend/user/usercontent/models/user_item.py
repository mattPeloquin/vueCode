#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Track user's content usage
"""
import json
from django.db import models

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common import sys_options
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.utils import now
from mpframework.common.utils import timedelta_seconds
from mpframework.common.utils import seconds_to_minutes
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.models import Tree
from mpextend.product.account.models import APA

from .user_item_manager import UserItemManager


class UserItem( SandboxModel ):
    """
    Tie user to content while tracking progress and other usage data.
    UserItem records are used for BOTH items and TOP-LEVEL collections

    FUTURE - Separate top-level collection and item usage models?
    FUTURE - support percent completion in the data for collections, maybe items
    FUTURE - move user item info in no-sql store

    There is only one record for each user and content item or collection,
    created when the user first accesses content.
    User content rows are deleted whenever user or content is deleted.
    """

    # The MTM relationship to content
    cu = models.ForeignKey( 'usercontent.ContentUser', models.CASCADE,
                            verbose_name=u"User" )
    item = models.ForeignKey( 'mpcontent.BaseItem', models.CASCADE,
                              verbose_name=u"Content" )

    # LAST top-level collection usage of the content item (if through a collection)
    # Normally null if item is a top tree, can also be null if the item is content
    # used in portal without a collection
    top_tree = models.ForeignKey( 'usercontent.UserItem', models.SET_NULL,
                                  related_name='_all_user_items',
                                  null=True, blank=True,
                                  verbose_name=u"Collection" )

    # The number of times the user has accessed the content
    # User item records are created on first access, but are not updated until the user
    # has engaged with content in UI (and content, APA is set). There are edge cases where
    # the record is created but not updated, in which case it is not visible in reporting
    uses = models.IntegerField( default=0 )

    # Item progress state; maps to UI display and completion calculations
    PROGRESS = (
        ( 'A', u"Accessed" ),  # For items without time element (e.g., downloads)
        ( 'S', u"Started" ),   # Item requires completion, and collections
        ( 'C', u"Completed" ), # Item can be finished / all items in collection done
        )
    progress = models.CharField( max_length=1, choices=PROGRESS )

    # Record the last update as the last time item was used
    last_used = mpDateTimeField( db_index=True, default=now )

    # When the content item was first completed
    completed = mpDateTimeField( null=True, blank=True )

    # Track rough approximation of seconds with item up by looking at
    # time between updates from browser
    seconds_used = models.IntegerField( default=0 )

    # Blob text/number/JSON data content can use to store state (LMS, video position, etc.)
    progress_data = models.TextField( blank=True )

    # Record the method of last progress adjustment, to identify manual completion
    PROGRESS_UPDATE = (
        ( 'S', u"System" ), # Programatic update by content rules
        ( 'U', u"User" ),   # User changed their progress
        ( 'A', u"Admin" ),  # Admin adjusted the progress
        )
    progress_update = models.CharField( max_length=1, default='S', choices=PROGRESS_UPDATE )

    # Core overall rating for item
    # This is used both for internal metrics as well as calculating
    # PUBLIC STAR DISPLAYS
    # This piece is the most important, so we'll require it before any other
    # feedback is collected
    FEEDBACK_ONE = 0
    FEEDBACK_TWO = 2
    FEEDBACK_THREE = 5
    FEEDBACK_FOUR = 8
    FEEDBACK_FIVE = 10
    FEEDBACK = (
        ( FEEDBACK_ONE, u"One Star" ),
        ( FEEDBACK_TWO, u"Two Star" ),
        ( FEEDBACK_THREE, u"Three Star" ),
        ( FEEDBACK_FOUR, u"Four Star" ),
        ( FEEDBACK_FIVE, u"Five Star" ),
        )
    feedback = models.IntegerField( choices=FEEDBACK, null=True, blank=True )

    # Blob data for detailed feedback form
    # This will allow creation of custom comment forms without modifying
    # the database (this could be an area with lots of change)
    feedback_data = YamlField( max_length=mc.TEXT_LEN_MED, null=True, blank=True )

    # Simple workflow for backoffice human review of feedback
    FEEDBACK_STATE = (
        ( '', u"No feedback" ),   # No feedback provided
        ( 'N', u"New" ),          # New feedback
        ( 'F', u"Flagged" ),      # Has been reviewed, want to do something
        ( 'C', u"Complete" ),     # No more action is needed
        )
    feedback_state = models.CharField( max_length=1, choices=FEEDBACK_STATE, default='', blank=True )

    # The LAST APA this content was used under
    # This used to be a MTM field, to support tracking amount of usage across time
    # (e.g., from free trial into paid licenses, etc). That level of granularity wasn't
    # providing value in business cases, so extra complexity was jettisoned
    # FUTURE - implement tracking of APA across time in time series data
    apa = models.ForeignKey( 'account.APA', models.SET_NULL,
                             null=True, blank=True,
                             verbose_name=u"License" )

    # Optional ID used by some content track current content version
    item_version = models.IntegerField( db_index=True, blank=True, null=True )

    class Meta:
        verbose_name = u"Content use"
        verbose_name_plural = u"Content usage"
        unique_together = ( 'cu', 'item' )

    objects = UserItemManager()

    # Normally when useritem needed, already have user, item
    select_related = ()
    # Support display of info in admin list
    select_related_admin = select_related + (
                'cu', 'cu__user',
                'item', 'item___django_ctype',
                'top_tree', 'top_tree__item',
                'apa',
                )

    def __str__( self ):
        if self.dev_mode:
            return "UIT: {}({})".format( self.item, self.pk )
        return str( self.item )

    def save( self, *args, **kwargs ):
        """
        Update time option should only be used when the last_used date
        has been set appropriately, such as before content access
        """
        # On first save, set item state based on completion type
        if not self.progress:
            self.progress = 'S' if self.item.can_complete else 'A'

        # Make sure progress data is valid
        if self.progress_data and isinstance( self.progress_data, str ):

            # Assume if JSON looking data can't be run through JSON it is bad
            if self.progress_data.startswith('{'):
                try:
                    json.loads( self.progress_data )
                except Exception as e:
                    log.info("HEAL - Progress data bad json: %s -> %s", self, e)
                    self.progress_data = ''

            # Provide for optional deep cleaning based on known issues
            elif not self.sandbox.options['user.no_usage_clean']:
                # Captivate can corrupt its own data with undefined values
                if 'undefined' in self.progress_data:
                    log.info("HEAL - Progress data has an undefined: %s -> %s",
                                self, self.progress_data)
                    self.progress_data = ''

        super().save( *args, **kwargs )

    @property
    def is_complete( self ):
        """
        Provide binary completion that includes item that are not completable
        """
        return self.progress in 'CA'

    @property
    def minutes_used( self ):
        return seconds_to_minutes( self.seconds_used )

    @property
    def is_collection( self ):
        return self.item.is_collection

    @property
    def is_top_collection( self ):
        return self.is_collection and not self.top_tree_id

    def set_progress( self, progress_data=None ):
        """
        Handles API requests to update user information
        """
        log.info3("Updating UserItem progress: %s -> %s", self, progress_data)

        if self.top_tree_id:
            self.top_tree.set_progress()

        if progress_data is not None:
            self.progress_data = progress_data
        self._update_time()
        self.save()

    def update_usage( self, apa_id=None, tree_id=None ):
        """
        Update user item on each NEW access session (vs. updating ongoing use,
        which is driven by API calls from client, and calls set_progress)
        """
        run_queue_function( _update_usage, self.sandbox,
                    ui_id=self.pk, apa_id=apa_id, tree_id=tree_id)

    def _update_usage( self, apa_id=None, tree_id=None ):
        # Each time this is called is considered a "use" vs. the updates
        # that may occur during use for status or time increments
        self.uses += 1

        # If APA has changed, update
        if apa_id and apa_id != self.apa_id:
            apa = APA.objects.get_from_id( self.sandbox, apa_id )
            apa.item_first_use( self.item, self.cu.user )
            self.apa = apa

        # If handed BaseItem id for tree, update and set our top tree
        # Could reset an existing top to model user using item
        # under tree and then on its own, but do not to make
        # reporting favor collections
        if tree_id:
            self._update_top_collection( tree_id )

        # Bring version up to latest if it was blanked due to removal
        if self.item_version is None:
            log.debug("HEAL - UserContent version: %s", self)
            self.update_version()

        self._update_time()
        self.save()

    def _update_top_collection( self, tree_id ):
        """
        Update the information for the top collection user item for
        this user item - this causes all content usage under a given
        top collection to be rolled up in one place.
        It also ensures the top collection is marked as used if any
        content inside it has been utilized.

        FUTURE - for now, the top collection APA simply reflects the LAST APA used
        with any item in the collection; this breaks down if users do a lot of
        splitting products across items inside a collection, which should be rare.
        """
        tree = Tree.objects.get_quiet( id=tree_id )
        if not tree:
            log.warning("Updating user content, missing tree: %s -> %s", self, tree_id)
            return
        root = tree.my_top
        top_tree = UserItem.objects.get_user_item( self.cu, root.pk, create=True )
        if top_tree:
            top_tree.uses += 1
            top_tree._update_time()
            if self.apa_id != top_tree.apa_id:
                top_tree.apa_id = self.apa_id
            top_tree.save()
            self.top_tree = top_tree

    def _update_time( self ):
        """
        Update model with approximation for tracking the number of seconds
        user has spent with content
        """
        time_now = now()
        delta_seconds = timedelta_seconds( time_now - self.last_used )

        # Avoid bad times from short times on content
        if delta_seconds < 1:
            log.debug("User item time too small: %s -> %s", self, delta_seconds)
            delta_seconds = 1

        # Avoid capturing seconds for idle workstations
        elif delta_seconds > sys_options.tracking_inactive_delta():
            log.debug("User item time too big: %s -> %s", self, delta_seconds)
            delta_seconds = sys_options.tracking_inactive_placeholder()

        log.debug("TRACKING %s -> %s to %s, added %s to %s", self, time_now,
                            self.last_used, delta_seconds, self.seconds_used)
        self.seconds_used += delta_seconds
        self.last_used = time_now

        # Support use metering
        if self.apa:
            self.apa.item_seconds_use( self.item, self.cu.user, delta_seconds )

    def set_feedback( self, rating=None, data=None ):
        log.info3("Updating UserItem feedback: %s, %s", rating, data)
        self.feedback_state = 'N'
        if rating:
            self.feedback = rating
        if data:
            self.feedback_data = data
        self.save()

    def update_version( self, version=None ):
        """
        Update version reference to given or or most recent
        """
        if not version:
            version = self.item.version
        log.info2("Updating UserItem version: %s -> %s", self, version)
        self.item_version = version
        return self.item_version

    def complete( self, progress_data=None ):
        """
        Handles API completion notices
        """
        self.completed = now()
        self.progress = 'C'
        self.set_progress( progress_data )


@mp_async
def _update_usage( **kwargs ):
    """
    Task for update user item data on first usage
    """
    t = mpTiming()
    log.debug("%s Starting user item update usage: %s", t, kwargs)
    kwargs.pop('my_task')
    ui_id = kwargs.pop('ui_id')

    ui = UserItem.objects.get( id=ui_id )
    ui._update_usage( **kwargs )

    log.info("<- %s User item usage: %s -> %s", t, ui, kwargs)
