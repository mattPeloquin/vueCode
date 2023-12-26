#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared user code for load testing
"""
import requests
from locust import HttpLocust
from django.utils.crypto import get_random_string

from ..content import PortalContent

# Don't want warnings from debug testing
requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning )


class UserLocust( HttpLocust ):

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.name = 'locust-{}'.format( get_random_string( 4 ).lower() )
        self.email = 'load_{}@vueocity.com'.format( self.name )
        self.csrf_headers = {}
        self.content = None
        self.current_item = None
        self.is_staff = False

    def get( self, url, name='', **kwargs ):
        kwargs['name'] = name
        return self.request( 'get', url, **kwargs )

    def post( self, url, data, name='', **kwargs ):
        kwargs['data'] = data
        kwargs['name'] = name
        return self.request( 'post', url, **kwargs )

    def patch( self, url, data, **kwargs ):
        kwargs['data'] = data
        return self.request( 'patch', url, **kwargs )

    def get_urls( self, urls, name='', **kwargs ):
        responses = []
        for url in urls:
            responses.append( self.get( url, **kwargs ) )
        if name:
            print( name, self.name, responses )
        return responses

    def request( self, method, url, **kwargs ):

        # Support debug site testing with *.mpd.xyz.com host names
        kwargs['verify'] = kwargs.pop( 'verify', 'mpd' not in self.host )

        kwargs['headers'] = kwargs.get( 'headers', {} )

        # Support simulating Ajax calls
        if kwargs.pop( 'ajax', False ):
            kwargs['headers']['X-Requested-With'] = 'XMLHttpRequest'

        # Add CSRF if available
        if self.csrf_headers and method in [ 'post', 'patch' ]:
            kwargs['headers'].update( self.csrf_headers )

        response = self.client.request( method, url, **kwargs )

        name = kwargs.get('name')
        if name: print( name, self.name, method, url, response )

        # Support CSRF saving with every call to simulate browser
        if response.ok and response.cookies and response.cookies.get('vueocity_csrf'):
            self.csrf_headers = {
                'referer': response.url,
                'x-csrftoken': response.cookies['vueocity_csrf'],
                }
        return response

    def new_user( self, url='/user/login' ):
        self.get( url )    # Force in case different csrf for site setup
        response = self.post( url, {
            'name': '',
            'new_user': self.email,
            'password1': 'mptest1',
            'create_code': 'mptest1',
            'create_user': 'LoadTest',
            })
        print("NEW USER", self.name, response )
        return response

    def login( self, url='/user/login' ):
        response = self.post( url, {
            'email': self.email,
            'password': 'mptest1',
            'login': 'LoadTest',
            })
        print("LOGIN", self.name, response )
        return response

    def logout( self, url='/user/logout' ):
        self.csrf_headers = {}
        print("LOGOUT {}".format( self.name ))
        return self.get( url )

    def load_portal( self, extra='' ):
        """
        Simulate loading portal, AND setup locust with information on this
        site's data for use in subsequent calls
        """
        responses = self.get_urls([
            '/' + extra,
            '/api/public/portal/bootstrap/content_TEST',
            '/api/public/portal/bootstrap/user_TEST',
            '/api/portal/bootstrap/nocache',
            ], "PORTAL")
        if responses[1].ok:
            bootstrap_content = responses[1].json()
            self.content = PortalContent( self, bootstrap_content )

    def access_item( self ):
        if self.content:
            self.current_item = self.content.access_item()

    def send_current_item_state( self ):
        if self.current_item:
            self.content.send_item_state( self.current_item )
