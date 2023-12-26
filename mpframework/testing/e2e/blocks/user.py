#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Blocks for login and user management
"""

from ..data import *
from ._base import SystemTestBlock


class UserBlock( SystemTestBlock ):
    """
    Represents a user in the system
    """

    def create_item( self, data=None, update=False ):
        """
        Create a new user from the given user data (or default)
        using the public create user page.
        NOTE - test data defaults beyond email will be set by default using
        the user profile menus, any other data must be updated with update.
        """
        if data:
            self.data = data.copy()
        if not self.data:
            self.data = get_unique_dict( USERS )

        self.stc.create_user( self )

        if update:
            self.update_portal()
            if self.is_staff:
                self.update_admin()

        self.stc.l("CREATED USER BLOCK: %s", self)
        return self

    def update_portal( self, data=None ):
        """
        Update the user data using the profile screens available to the user,
        uses either exists block data or an update
        """
        if data:
            self.data = data
        self.stc.get_css('.mp_user_name').click()
        self.stc.go_menu('profile')
        self.stc.get_id('id_first_name').send_keys( self.data['first_name'] )
        self.stc.get_id('id_last_name').send_keys( self.data['last_name'] )
        self.stc.get_name('update_profile').click()
        return self

    def login( self ):
        self.stc.login( self )

    @property
    def is_staff( self ):
        level = self.data.get('level')
        return level and 'No staff' not in level

    def verify_portal( self ):
        self.stc.get_css('.mp_user_name').click()
        self.stc.go_menu('profile')
        self.stc.assertTrue( self.data['email'] ==
                             self.stc.get_id('id_email').get_attribute('value'))
        self.stc.assertTrue( self.data['first_name'] ==
                             self.stc.get_id('id_first_name').get_attribute('value'))
        self.stc.assertTrue( self.data['last_name'] ==
                             self.stc.get_id('id_last_name').get_attribute('value'))

    #---------------------------------------------------------------
    # Methods below can only use used when a staff user is active

    def set_staff_level( self, level=None ):
        """
        Have current logged in user, set staff level
        Go to edit screen first, to make sure new staff are looked up in customer screen
        """
        self.go_edit()
        if not level and not self.data.get('level'):
            level = self.data.get( 'first_level', 'EasyVue' )
        self.stc.l("SETTING STAFF LEVEL: %s", level)
        self.data['level'] = level
        self.stc.click_dropdown( '#id__staff_level', self.data['level'] )
        self.stc.get_id('mpsave').click()

    def go_edit( self ):
        """
        Go to the admin edit page for the user
        """
        if self.is_staff:
            self.stc.go_menu('users', 'manage-staff')
        else:
            self.stc.go_menu('users', 'manage-users')
        self.stc.go_anchor( self.data['email'] )

        # TESTWORK NOW - add support for pagination/search when list is long
