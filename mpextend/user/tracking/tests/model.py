#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User tracking Model tests
"""
from mpframework.testing.framework import ModelTestCase

from ..models import UserTracking


class ModelTests( ModelTestCase ):

    def test_tracking( self ):

        staff_user = self.login_owner()
        tracking = staff_user.tracking
        self.assertTrue( tracking )
        self.assertTrue( tracking.logins == 1 )

        self.l("Testing session reduction")

        # By logging in and out, will create 3 user sessions
        # Assuming that active user sessions is set to 1, two
        # sessions will be set inactive
        self.login_user()
        self.logout()
        self.login_user()
        self.logout()
        user = self.login_user()

        # Tracking records are created/updated, but there shouldn't be multiple records
        sandbox_trackings = list( UserTracking.objects.recent_sandbox( user.sandbox ) )
        provider_trackings = list( UserTracking.objects.recent_provider( staff_user._provider ) )
        self.assertTrue( len(sandbox_trackings) == 1 )   # Only user from sandbox
        self.assertTrue( len(provider_trackings) == 2 )  # Includes the staff provider

        # Check for session reduction
        all_sessions = []
        active_sessions = []

        for ut in sandbox_trackings:
            for session in ut.sessions.values():
                all_sessions.append( session )
            active_sessions += ut.active_sessions
        active_sessions2 = [ session for session in all_sessions if session['active'] ]

        self.assertTrue( len(active_sessions) == len(active_sessions2) )

        self.wait_for_threads()

        print( ut.active_sessions, active_sessions2 )

        self.assertTrue( len(all_sessions) == 3 )
        self.assertTrue( len(active_sessions) == 1 )
