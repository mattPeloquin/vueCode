#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manage user badges
"""
from django.db import models

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.utils import now
from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import SandboxModel

from .badge import Badge


class UserBadge( SandboxModel ):
    """
    Track the badges a user has accumulated.
    User badge rows are deleted whenever user is deleted.
    """

    # The MTM relationship to badges
    cu = models.ForeignKey( 'usercontent.ContentUser', models.CASCADE,
                            verbose_name=u"User" )
    badge = models.ForeignKey( Badge, models.CASCADE,
                               verbose_name=u"Badge" )

    # Badge state
    PROGRESS = (
        ( 'S', u"Started" ),   # BadgeBot has noticed progress towards badge
        ( 'C', u"Completed" ), # User has completed badge
        )
    progress = models.CharField( max_length=1, choices=PROGRESS )

    # When badge was first completed
    completed = mpDateTimeField( null=True, blank=True )

    # Record the method of last badge adjustment, to identify manual completion
    PROGRESS_UPDATE = (
        ( 'S', u"System" ), # Programatic update by BadgeBot content rules
        ( 'A', u"Admin" ),  # Admin adjusted the progress
        )
    progress_update = models.CharField( max_length=1, default='S', choices=PROGRESS_UPDATE )

    # Blob text/number/JSON data content can use to store state (LMS, video position, etc.)
    progress_data = models.TextField( blank=True )

    class Meta:
        verbose_name = u"User badge"
        verbose_name_plural = u"User badges"
        unique_together = ( 'cu', 'badge' )

    objects = TenantManager()

    # Normally when userbadge accessed, already have user and badge
    select_related = ()
    # Support display of info in admin list
    select_related_admin = select_related + ( 'cu', 'cu__user', 'badge' )

    def __str__( self ):
        if self.dev_mode:
            return "UB: {}({})".format( self.badge, self.pk )
        return str( self.badge )

    @property
    def is_complete( self ):
        """
        Provide binary completion that includes item that are not completable
        """
        return self.progress in 'CA'

    def set_progress( self, progress_data=None ):
        """
        Handles requests to update user badge info
        """
        log.info3("Updating UserBadge: %s -> %s", self, progress_data)

        if progress_data is not None:
            self.progress_data = progress_data
        self._update()
        self.save()

    def update( self ):
        """
        Update the user item on each new (vs. ongoing use set progress)
        """
        run_queue_function( _update, self.sandbox, ui_id=self.pk )

    def _update( self ):

        # TBD - update the badge

        self.save()

    def complete( self, progress_data=None ):
        self.completed = now()
        self.progress = 'C'
        self.set_progress( progress_data )


@mp_async
def _update( **kwargs ):
    """
    Task update user badge
    """
    t = mpTiming()
    log.debug("%s Starting user badge update: %s", t, kwargs)
    kwargs.pop('my_task')
    ui_id = kwargs.pop('ui_id')

    ui = UserBadge.objects.get( id=ui_id )
    ui._update_usage( **kwargs )

    log.info("<- %s User badge update: %s -> %s", t, ui, kwargs)
