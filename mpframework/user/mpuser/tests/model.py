#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpUser Model tests
"""

from mpframework.testing.framework import ModelTestCase
from mpframework.foundation.tenant.models.sandbox import Sandbox

from ..models import mpUser
from ..utils.activate import activate_user


class ModelTests( ModelTestCase ):

    def test_mpuser(self):
        sand = Sandbox.objects.get( id=20 )

        self.l("Manipulate existing user object directly")

        u = mpUser.objects.get( id=1 )
        self.assertTrue( u )
        desc1 = str(u)
        self.assertTrue( desc1 )
        self.assertTrue( u.is_root_staff )
        self.assertTrue( u.access_root )

        u.update_username('changed_email')
        desc2 = str(u)
        self.assertTrue( desc1 != desc2 )

        self.l("Test user manager and caching")

        u1a = mpUser.objects.get_from_id( sand, 11 )
        u1b = mpUser.objects.get_from_id( sand, 11 )
        self.assertTrue( u1a.name == u1b.name )

        u1a.invalidate()
        u1a = mpUser.objects.get_from_id( sand, 11 )
        self.assertTrue( u1a == u1b )

        users = mpUser.objects.lookup_queryset( u1a.sandbox )
        self.assertTrue( users )

        bad_user = mpUser.objects.get_from_id( sand, 123456 )
        self.assertFalse( bad_user )

        self.l("Test via test login spoofing")

        u = self.login_owner()
        self.assertTrue( u )
        self.assertTrue( u.pk == 12 )
        self.assertTrue( u.provider.pk == 11 )
        self.assertTrue( u.is_owner )
        self.assertTrue( u.is_staff )
        self.assertFalse( u.workflow_dev )
        self.assertTrue( u.sees_content )
        self.assertTrue( u.sees_user )
        self.assertTrue( u.sees_licensing )
        self.assertTrue( u.sees_sandbox )

        u = self.login_owner( id=15, sandbox_id=30 )
        self.assertTrue( u )
        self.assertTrue( u.pk == 15 )
        self.assertTrue( u.provider.pk == 12 )
        self.assertTrue( u.sees_content )
        self.assertFalse( u.sees_user )
        self.assertTrue( u.sees_licensing )
        self.assertFalse( u.sees_sandbox )

        self.l("Create new user")

        u = mpUser.objects.create_obj( email="new_user_email", password=self.TEST_PWD,
                                       sandbox=sand )
        self.assertTrue( u )
        self.assertTrue( u.username == "new_user_email"  )
        self.assertFalse( u.is_root_staff )
        self.assertFalse( u.is_owner )
        self.assertFalse( u.is_superuser )
        self.assertFalse( u.is_staff )
        self.assertFalse( u.logged_into_root )
        self.assertFalse( u.sees_sandboxes )

        activate_user( u, sand )
        u = self.login_user( u.pk )
