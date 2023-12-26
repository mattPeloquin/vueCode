#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for user content models and related application tests
"""

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh

from ..models import ContentUser


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Visitor content")
        self.sandbox_init()
        self._user_urls( access=False, ready=False )

        self.l("User access of user content")
        self.login_user()
        self._user_urls( access=False )

        if self.test_level:
            self.login_nogroup()
            self._user_urls( access=False )
            self.login_notready()
            self._user_urls( access=False, ready=False )

        self.l("Staff access")
        self.login_staff()
        self._staff_urls()

        if self.test_level:
            self.l("Root access of user content")
            self.login_root()
            self._staff_urls()
            self.app_root_urls_test('usercontent')
            self._user_urls()

            self.l("Provider admin updating user content")
            self.login_owner()
            self._staff_urls()
            self.fetch_put( '/api/uc/user_items/1101',
                        '{"id": "1101", "status": "C"}' ) # Must be a json string

    def _user_urls( self, access=True, ready=True ):

        rv = self.fetch_get( reverse('api_item_access'), {'id': ''}, fail=True )
        self.assertFalse( rv )

        # free_public and free_user content checks
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1202} )
        self.assertTrue( rv['can_access'] == True )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1301} )
        self.assertTrue( rv['can_access'] == True )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1203} )
        self.assertTrue( rv['can_access'] == ready )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1101} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1101, 'tree_id': 1001} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1201} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1351} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1501} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1601} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1701} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1801} )
        self.assertTrue( rv['can_access'] == access )
        rv = self.fetch_post( reverse('api_item_access'), {'id': 1901} )
        self.assertTrue( rv['can_access'] == access )

    def _staff_urls( self ):

        self.app_staff_urls_test('usercontent')

        self.fetch_post( bh('/api/uc/update_version'), {'item_id': 1101} )
