#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    High-level, broad tests to quickly check basic functionality
"""

from mpframework.testing.e2e.tests.base import SystemTestCase
from mpframework.testing.e2e import stories


@SystemTestCase.register
class VueBasicSmokeTests( SystemTestCase ):

    def test_products( self ):
        """
        Use the EasyVue Add Product screen to create products, and then
        update their content and catalog items, verifying along the
        way in both the portal and admin screens
        """
        self.owner.login()
        self.l(">>> Creating products")
        products = stories.new_products( self, 1, verify=True )

        def _verify( staff=False, full=False ):
            """
            Accesses content for products through portal using
            both staff and a new user. Do the user first, so the
            staff member ends up logged in
            """
            self.l(">>> Verifying products with new user")
            stories.login_user( self )
            for pb in products:
                pb.verify_portal()

            self.l(">>> Verifying products with staff: %s", staff)
            staff = staff or self.owner
            staff.login()
            for pb in products:
                pb.verify_portal()
                pb.verify_admin( full )

        self.set_window_small()
        self.l(">>> Update and edit product content and pricing")
        stories.edit_content( self, products )
        stories.edit_pricing( self, products )
        _verify()

        self.set_window_norm()
        self.l(">>> New staff update and edit product content and pricing")
        staff = stories.new_staff( self )
        stories.edit_content( self, products )
        stories.edit_pricing( self, products )
        _verify( staff, True )









