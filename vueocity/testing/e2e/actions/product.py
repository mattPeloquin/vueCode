# --- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Product test actions
"""

from mpframework.testing.e2e import stories


class ProductActions:

    def action_create_products( self ):
        self.l( ">>> Creating products" )

        def _user_verify( products ):
            stories.login_user( self )
            for pb in products:
                pb.verify_portal()
            self.owner.login()

        self.owner.login()
        self.set_window_random()
        products = stories.new_products( self, self.NUM_RUNS, verify=True )
        _user_verify( products )

        stories.edit_content( self, products )
        stories.edit_pricing( self, products )
        _user_verify( products )
