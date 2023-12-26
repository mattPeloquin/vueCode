#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content view tests

    FUTURE - Some content tests have dependency on extend test data
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh

from ..models import ProtectedFile


class ViewTests( ViewTestCase ):

    def test_access( self ):
        # FUTURE - Simulate user accessing content through CF signed cookie redirect

        self.l("Testing content access urls - user")
        self.login_user()
        self._access_urls()
        if self.test_level:
            self._test_api( fail=True )

        self.l("Testing content access urls - staff")
        self.login_staff_low()
        self._access_urls()
        self._test_api()

        if self.test_level:
            self.login_root()
            self._access_urls()
            self._test_api( root_fail=False )

    def _access_urls( self ):

        sand = self.current_user.sandbox
        f1 = ProtectedFile.objects.create_obj( sandbox=sand,
                content_file='Test.File', name='TestFile' )
        self.get_url( '/portal#view-file-{}'.format( f1.pk ) )

    def _test_api( self, fail=False, root_fail=True ):
        self.l("Testing tree set workflow")
        rv = self.fetch_post( bh('/api/content/tree_set_workflow'),
                    {'tree_id': 1008, 'workflow_level': 'P'}, fail=fail )
        not fail and self.assertTrue( 'Collection2aa' in rv['item_names'] )
        not fail and self.assertTrue( 'WordS20free' in rv['item_names'] )

        self.l("Trying to set value outside sandbox should fail")
        rv = self.fetch_post( bh('/api/content/tree_set_workflow'),
                    {'tree_id': 1014, 'workflow_level': 'P'}, fail=True )
        self.assertFalse( rv )

        self.l("Move items in and out of retirement")
        rv = self.fetch_post( bh('/api/content/tree_set_workflow'),
                    {'tree_id': 1010, 'workflow_level': 'Q'}, fail=fail )
        not fail and self.assertTrue( rv['update_count'] == 4 )
        rv = self.fetch_post( bh('/api/content/tree_set_workflow'),
                    {'tree_id': 1010, 'workflow_level': 'B'}, fail=fail )
        not fail and self.assertTrue( rv['update_count'] == 4 )

        self.l("Testing tree set sandboxes")
        rv = self.fetch_post( bh('/api/content/tree_set_sandboxes'),
                    {'tree_id': 1008, 'sandbox_ids': '[20, 21]' }, fail=fail )
        not fail and self.assertTrue( 'Collection2aa' in rv['item_names'] )
        not fail and self.assertTrue( 'WordS20free' in rv['item_names'] )
        rv = self.fetch_post( bh('/api/content/tree_set_sandboxes'),
                    {'tree_id': 1008, 'sandbox_ids': '[20]' }, fail=fail )
        not fail and self.assertTrue( 'Collection2aa' in rv['item_names'] )

        self.l("Tree set sandbox outside sandbox should fail")
        rv = self.fetch_post( bh('/api/content/tree_set_sandboxes'),
                    {'tree_id': 1014, 'sandbox_ids': '[20, 21]' }, fail=True)
        self.assertFalse( rv )

        self.l("Testing tree rebuild")
        rv = self.fetch_post( bh('/api/content/tree_rebuild'),
                    {'tree_top_id': 1007 }, fail=root_fail )
        not root_fail and self.assertTrue( rv['rebuilt'] )
        rv = self.fetch_post( bh('/api/content/tree_rebuild'),
                    {'tree_top_id': 1008 }, fail=root_fail )
        not root_fail and self.assertFalse( rv['rebuilt'] )

        self.l("Tree rebuild outside sandbox should fail")
        rv = self.fetch_post( bh('/api/content/tree_rebuild'),
                    {'tree_top_id': 1014 }, fail=True)
        self.assertFalse( rv )

        if not fail:
            self.l("Autolookup tests")
            self.autolookup_get( 'mpcontent', 'baseitem', '' )
            self.autolookup_get( 'mpcontent', 'baseitem', 'a' )


    def test_staff( self ):

        self.l("Content staff screens")
        self.login_owner()
        self._content_urls()
        self.app_staff_urls_test('mpcontent')

        self.l("Content visitor views")
        self.sandbox_init()
        self._content_urls()

        if self.test_level:
            self.app_staff_urls_test('mpcontent', fail=True)

            self.l("Content user views")
            self.login_user()
            self._content_urls()
            self.app_staff_urls_test('mpcontent', fail=True)
            self.app_root_urls_test('mpcontent', fail=True)

            self.l("High and low content staff screens")
            self.login_staff_high()
            self.app_staff_urls_test('mpcontent')
            self._content_urls()
            self.login_staff_low()
            self.app_staff_urls_test('mpcontent')
            self._content_urls()

            self.l("Root content screens")
            self.login_root( 30 )
            self.app_staff_urls_test('mpcontent')
            self.app_root_urls_test('mpcontent')
            self._content_urls()

            self.login_root()
            self.app_root_urls_test('mpcontent')

    def _content_urls( self ):

        self.ld("Public content access")

        content = self.fetch_get( reverse('api_get_content') )
        self.assertTrue( len(content['collections']) > 2 )

        info = self.fetch_get( reverse( 'api_content_full',
                kwargs={ 'content_slug': 'TESTtag' } ) )
        self.assertTrue( info['name'] == "A Test Collection" )

        info = self.fetch_get( reverse( 'api_content_partial',
                kwargs={ 'content_slug': '1001' } ) )
        self.assertTrue( info['name'] == "A Test Collection" )
