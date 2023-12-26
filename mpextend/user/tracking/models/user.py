#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User Tracking logic and persisted data
"""
from django.db import models
from django.conf import settings
from django.contrib.sessions.backends.cache import SessionStore

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common import sys_options
from mpframework.common.utils import now
from mpframework.common.utils import timedelta_seconds
from mpframework.common.utils import seconds_to_minutes
from mpframework.common.model import BaseModel
from mpframework.common.model.fields import mpOneToOneField
from mpframework.common.model.fields import TruncateCharField
from mpframework.user.mpuser.models import mpUser

from .tracking_base import BaseTracking
from .tracking_manager import UserTrackingManager


class UserTracking( BaseTracking, BaseModel ):
    """
    State and tracking information persisted for user.

    One tracking row is normally in place for every user, aggregating
    information about the user's sessions.
    Tracking rows may be deleted without impacting the core user records.
    """
    user = mpOneToOneField( mpUser, models.CASCADE, related_name='tracking' )

    # Rough attempt to track active time between requests
    seconds = models.IntegerField( db_index=True, default=0 )

    # Per-user client UI options/state, managed as JSON blob data by JS UI code
    ui_state = TruncateCharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    # Values for DB sorting or searching
    logins = models.IntegerField( db_index=True, default=0 )

    objects = UserTrackingManager()
    select_related = ( 'user' ,)

    def __str__( self ):
        # Only directly visible in root/debug/log
        return "{} {}".format( self.user.log_name, self.ip_address )

    def update_state( self, ui_state ):
        """
        Update of UI state, which happens via ajax
        """
        log.debug("Updating tracking state: %s -> %s", self, ui_state)
        self.ui_state = ui_state
        self.set_time( now( use_ms=True ) )
        self.save()
        return self.last_update

    def reduce_extra_sessions( self, current_session_key, maximum=None ):
        """
        If there are active session objects for this user tracking
        delete any above maximum number -- removing oldest first
        Info for recent deleted sessions are left,
        as old records provide tracking information
        """

        # Staff users can have up to system maximum sessions
        # Allow sandbox to move session limit up from default, but
        # not higher than max to avoid abuse of active user tracking
        max_sessions = settings.MP_TRACKING['SESSIONS_MAX']
        if not self.user.is_staff:
            if maximum and maximum < max_sessions:
                max_sessions = maximum
            else:
                max_sessions = settings.MP_TRACKING['SESSIONS_DEFAULT']

        sessions = self.session_list
        if len( sessions ) > max_sessions:
            try:
                self._reduce_sessions( sessions, current_session_key,
                            max_sessions )
                log.info2("Session reduce complete: %s", self )
            except Exception as e:
                log.warning("SUSPECT - Error reducing sessions: %s -> %s",
                            self.user, e)

    def _reduce_sessions( self, sessions, current, max_num ):
        dirty = False
        active_count = 0
        old_count = 0
        for session in sessions:
            log.debug2("recent_session: %s", session)
            key = session['key']
            # Skip the current session
            if key == current:
                assert session['active']
                active_count += 1
                continue
            # Deactivate extra active user sessions to prevent sharing of accounts
            if session['active']:
                active_count += 1
                if active_count > max_num:
                    log.info2("Reducing extra user session: %s -> %s", self, key)

                    SessionStore( key ).delete()

                    # Mark as inactive in the user tracking
                    session.update({ 'active': False })
                    self.sessions.update({ key: session })
                    dirty = True
            # Remove old session information
            else:
                old_count += 1
                if old_count > settings.MP_TRACKING['SESSIONS_OLD']:
                    log.info2("Removing old user session tracking: %s -> %s", self, key)
                    self.sessions.pop( key, None )
                    dirty = True
        if dirty:
            self.save()

    def force_logout( self ):
        """
        Force user logout by inactivating all sessions
        """
        sessions = self.session_list
        if not sessions:
            return
        log.info("LOGOUT forcing: %s (%s sessions)", self, len(sessions))

        for session in sessions:
            log.debug("Killing session: %s", session)
            key = session['key']
            SessionStore( key ).delete()

            # Mark as inactive in the user tracking
            session.update({ 'active': False })
            self.sessions.update({ key: session })

        self.save()

    @property
    def minutes( self ):
        return seconds_to_minutes( self.seconds )

    def set_time( self, time_now ):
        """
        Update time with time since last active use.
        To deal with client-side inactivity that isn't detected and/or long gaps
        in session span, a crude max active time delta is used
        """
        new_seconds = timedelta_seconds( time_now - self.last_update )
        if new_seconds > sys_options.tracking_inactive_delta():
            log.debug("User tracking reducing %s -> %s", self, new_seconds)
            new_seconds = sys_options.tracking_inactive_placeholder()

        log.debug("TRACKING %s -> last: %s, adding %s to %s",
                    self, self.last_update, new_seconds, self.seconds)
        self.seconds += new_seconds
