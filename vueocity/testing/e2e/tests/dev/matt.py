#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Matt's test sandbox
"""

from mpframework.testing.e2e.tests.base import SystemTestCase


@SystemTestCase.register
class MattTests( SystemTestCase ):

    def test_1( self ):
        self.owner.login()

        self.get_id( 'foo', show_hidden=True)


        """

        self.sb.menu( 'users', 'manage-users' )
        self.go_anchor('user@acme.com')
        self.click_dropdown( '#id_staff_level', 'EasyVue' )

        """


    """
    def test_visitor( self ):
        self.l("Testing visitors")
        self.logout()
        self.go_home()
        self.try_content( access=False )

    def test_root( self ):
        self.l("Testing root user")
        self.login_user('root@mp.com')
        self.try_content()

    def test_new( self ):
        self.l("Testing new user")
        self.create_user('new@user.com')
        self.try_content( access=False )

    def try_content( self, access=True ):
        self.wait()

        self.get_content_text('A Test Collection').click()
        self.wait()

        item = self.get_class('es_code_PPT-S20')
        item.click()
        self.wait()

        if access:
            self.sln.back()
        else:
            self.escape()
            self.wait(0.5)
            item.click()
    """
