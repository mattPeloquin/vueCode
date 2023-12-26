#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base class for all E2E test cases
    Those system test cases are then mixins for System Internal/External classes
"""

from mpframework.testing.framework.testcase.mixin import mpTestCaseMixin
from mpframework.testing.e2e.blocks import UserBlock

# Import all data to be visible in all test case files
from mpframework.testing.e2e.data import *


class SystemTestCase( mpTestCaseMixin ):
    """
    Shared mixin base class code that extends MPF Selenium test support
    with general framework-specific logic.
    All system test case classes inherit from this, and will then be registered
    as Selenium Internal/External classes at run time with the test runner.
    """

    @staticmethod
    def register( test_class ):
        """
        Class decorator used to designate the type of test case (internal/external).
        by mapping a test case class from a test module onto system test classes
        that are loaded by the SystemTest test runner.
        """
        try:
            import sys
            from ...framework.testcase.system import (
                        SystemInternalTestCase,
                        SystemExternalTestCase,
                        )
            test_class_module = sys.modules[ test_class.__module__ ]
            setattr( test_class_module, 'SystemInternalTests',
                     type( 'SystemInternalTests', ( test_class, SystemInternalTestCase ), {} )
                     )
            setattr( test_class_module, 'SystemExternalTests',
                     type( 'SystemExternalTests', ( test_class, SystemExternalTestCase ), {} )
                     )
        except Exception as e:
            print("Exception loading test class: %s -> %s" % (test_class, e))
            import traceback
            traceback.print_exc()

    def setUp( self ):
        """
        Setup test case for new sandbox or local test fixture
        """
        super().setUp()
        self.current_user = None

        # Register all actions
        self.actions = []
        for name in dir( self ):
            if name.startswith('action_'):
                self.actions.append( name )

        # The user that owns the sandbox for the test case
        owner_data = getattr( self, 'owner_data', STAFF['SBPRO'] )
        self.owner = UserBlock( self, owner_data, create=False )

        # Setup a new site if requested using provider onboard screen
        # This is here instead of in a story because it is outside sandbox tests
        if self.owner.data.get('new'):
            exists = self.go_home()
            if not exists:
                self.go_url( self.server_url + '/portal/sign_up', full=True )
                self.get_name('subdomain').send_keys( self.owner.data.get('site_subdomain') )
                self.get_name('email').send_keys( self.owner.data.get('email') )
                self.get_name('password1').send_keys( self.owner.data.get('password') )
                self.get_name('start_trial').click()
                self.wait_point( 2 )

        # HACK - used fixture data with local test
        elif any( local in self.site_url for local in ['localhost', '127.0.0.1' ] ):
            self.owner.data['email'] = 'staff@p1.com'
            self.owner.data['password'] = 'mptest'

    #-----------------------------------------------------------------
    # User actions

    def login( self, user, force=False ):
        """
        Logs user block user in via the login page
        Tracks current user block and just goes home if already logged in
        """
        self.l("LOGIN %s", user)
        if not force and self.current_user == user:
            self.go_home()
            return

        # Force logout and url to go to login screen, and do click on
        # user create switch if wrong panel is showing
        self.logout()
        self.click_css( '#user_create .mp_user_switch', wait=0 )
        self.get_id('id_email').send_keys( user.data['email'] )
        self.get_id('id_password').send_keys( user.data['password'] )
        self.wait_point()
        self.get_name('login').click()
        self.current_user = user

    def create_user( self, user ):
        """
        Creates (and logs in) new user via the create user page
        """
        self.logout()

        self.l("CREATE USER: %s", user)
        self.click_css( '#user_auth .mp_user_switch', wait=0 )
        self.get_id('new_new_user').send_keys( user.data['email'] )
        self.get_id('new_password1').send_keys( user.data['password'] )
        self.wait_point()
        self.get_name('create_user').click()
        self.current_user = user

    def logout( self ):
        self.go_url( '/user/logout', refresh=True )
        self.current_user = None

    #-----------------------------------------------------------------
    # Navigation aids

    def go_home( self ):
        return self.go_url('/', refresh=True)

    def go_login( self, sku=None ):
        login_url = '/user/login'
        if sku:
            login_url = '{}/sku/{}'.format( login_url, sku )
        return self.go_url( login_url )

    def go_menu( self, *args, **kwargs ):
        """
        Navigate staff menu through a series of clicks
        """
        self.l("STAFF MENU: %s", args)
        for menu in args:
            menu_id = 'menu_{}'.format( menu )
            menu = self.get_id( menu_id, required=False, wait=0, log=False )
            if not menu:
                # Make sure the menu is open if collapsed
                self.get_xpath(
                        '//*[@id="{}"]/ancestor::*[@class="mp_menu"]'
                            '/ancestor::*[ @class="mpr_collapse" and '
                            'not(@class="mpr_collapse_open") ]'.format( menu_id ),
                        required=False, wait=0, log=False ).click()
                menu = self.get_id( menu_id, log=False, **kwargs )
            self.wait_point()
            menu.click()
        self.wait_point()

    def go_portal( self ):
        """
        Go to portal with options to modify display options
        """
        url = '/portal'
        return self.go_url( url )

    #-----------------------------------------------------------------
    # Special portal commands

    # Find content items by values
    def get_content_id( self, id ):
        return self.get_css( '.es_content.es_id_{}'.format( id ) )
    def get_content_code( self, code ):
        return self.get_css( '.es_content.es_code_{}'.format( code ) )
    def get_content_text( self, text ):
        return self.get_class_text( 'es_content', text )

    def template_select( self, template='' ):
        """
        Change the portal template on staff menus
        """
        id = 'portal'
        if template:
            id = id + '_{}'.format( template )
        template_menu = self.menu( id )
        template_menu.click()

    def content_toggle_A( self ):
        self.get_css('.mpp_toggle_A').click()
    def content_toggle_B( self ):
        self.get_css('.mpp_toggle_B').click()
