#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpUser extension tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


def new_user():
    global user_num
    user_num += 1
    return {
        'create_user': '',
        'new_user': f'new{ user_num }@user.com',
        'password1': 'test123',
        }
user_num = 0


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Login create tests")

        self.sandbox_init()
        self.post_url( reverse('login_create'), data=new_user() )

        self.sandbox_init( reset=True )
        self.post_url( reverse('login_sku', kwargs={ 'sku': 'BuyPA_10' }),
                    data=new_user(), redirects=1 )
        apas = self.fetch_get( reverse('api_access_apas') )
        self.assertFalse( 'BuyPA_10' in apas )

        self.sandbox_init( reset=True )
        self.post_url( reverse('login_sku', kwargs={ 'sku': 'FreePA_11' }),
                    data=new_user(), redirects=1 )
        apas = self.fetch_get( reverse('api_access_apas') )
        self.assertTrue( 'FreePA_11' in apas )
