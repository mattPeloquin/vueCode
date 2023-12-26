# --- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Uses an owner to create new products in a loop
"""

from mpframework.testing.e2e import stories


class ContentActions:

    def action_create_content( self ):
        self.l( ">>> Creating content" )

        def _user_verify( content ):
            stories.login_user( self )
            for cb in content:
                cb.verify_portal()
            self.owner.login()

        self.owner.login()
        self.set_window_random()
        content = stories.new_content( self, self.NUM_RUNS, verify=True )
        _user_verify( content )

