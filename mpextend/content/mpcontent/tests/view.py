#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for content models and related application tests
    Note that admin URLs get tested in the base admin test
    introspection, even though most item classes are
    defined here
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh


class ViewTests( ViewTestCase ):

    def test_content_endpoints( self ):

        self.l("Testing content urls - visitor")
        self.sandbox_init()
        self._bootstrap_timewin()
        self._access_urls()
        if self.test_level:
            self._api_urls()

        self.l("Testing content urls - user")
        self.login_user()
        self._bootstrap_timewin()
        self._access_urls()
        self._api_urls()

        self.l("Testing content urls - staff")
        self.login_staff_low()
        self._bootstrap_timewin()
        self._access_urls()
        self._api_urls( staff=True )

    def _access_urls( self ):
        self.l("Access URLs")
        # Also coverage is under api_item_access in usercontent

        self.get_url('/portal/vue+video-1101')
        self.get_url('/portal/vue+video-1201')
        self.get_url('/portal/vue+video-1301')
        self.get_url('/portal/vue+video-1301-1001')
        self.get_url('/portal/vue+video-1351')
        self.get_url('/portal/vue+video-1701')
        self.get_url('/portal/vue+video-1801')

    def _api_urls( self, staff=False ):
        self.l("Content APIs")

        response = self.fetch_get( bh('/api/lms/package_metrics'),
                    {'lms_id': 1101}, fail=not staff )
        if staff:
            self.assertTrue( 'LMSTEST' in response['package_metrics_dict'] )

        self.l("Add item to content")
        response = self.fetch_post( bh('/api/content/item_add'),
                    {'item_type': 'video'}, fail=not staff)
        if staff:
            info = self.fetch_get( reverse('api_content_partial',
                    kwargs={ 'content_slug': response['new_item_id'] } ) )
            self.assertTrue( 'New Video' in info['name'] )
            bootstrap = self._bootstrap_delta()
            self.assertTrue( 'New Video' in str(bootstrap) )
        else:
            self.assertTrue( response is None )

        self.l("Add item to tree")
        name = 'NewEmbedName'
        response = self.fetch_post( bh('/api/content/item_add'),
                    {'tree_id': 1008, 'item_type': 'embed', 'name': name },
                    fail=not staff )
        if staff:
            info = self.fetch_get( reverse('api_content_full',
                    kwargs={ 'content_slug': response['new_item_id'] } ) )
            self.assertTrue( name in info['name'] )
            bootstrap = self._bootstrap_delta()
            self.assertTrue( name in str(bootstrap) )
        else:
            self.assertTrue( response is None )

        self.l("Clone item to tree")
        response = self.fetch_post( bh('/api/content/item_add'),
                    {'tree_id': 1008, 'clone_id': 1201 }, fail=not staff )
        if staff:
            response = self.fetch_get( reverse('api_content_partial',
                            kwargs={ 'content_slug': response['new_item_id'] } ) )
            self.assertTrue( 'PPT' in response['name'] )
        else:
            self.assertTrue( response is None )


    def _bootstrap_timewin( self ):
        # Call bootstrap content to setup a timewin
        return self.fetch_get( reverse('bootstrap_content') )

    def _bootstrap_delta( self ):
        # Bootstrap content change is in timewin delta
        return self.fetch_get( reverse('bootstrap_delta') )
