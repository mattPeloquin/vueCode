#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Onboard model tests
"""

from mpframework.testing.framework import ModelTestCase
from mpframework.user.mpuser.models import mpUser

from ..clone import onboard_clone


class ModelTests( ModelTestCase ):

    def test_onboard( self ):
        email = 'newowner@email.com'

        self.sandbox_init( 20, reset=True )

        s = onboard_clone( self.current_sandbox, 'TestCloneSandbox',
                'TestSubdomain', 'TestOnboardRole', email, 'newpass' )
        self.assertTrue( s )
        self.assertTrue( s.pk != 20 )
        self.assertTrue( s.subdomain == 'TestSubdomain' )

        u = mpUser.objects.get_user_from_email( email, s )
        self.assertTrue( u )
        self.assertTrue( u.is_ready() )
        self.assertTrue( u.is_staff )
        self.assertTrue( u.email == email )
        self.assertTrue( u.provider == s.provider )

        s2 = onboard_clone( self.current_sandbox, 'http::\\BadCloneSandbox',
                'TestSubdomain', 'TestOnboardRole', email, 'newpass' )
        self.assertFalse( s2 )
