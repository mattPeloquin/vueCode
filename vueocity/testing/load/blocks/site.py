#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared load test code for creating new sites
"""

from .. import bh


class TestSite:
    """
    Runs once to create a new demo site
    Only first staff locust for a site matters; other locusts may call again,
    but it will just fail.
    """
    create_url = bh('/public/ob/onboard_signup')
    site_created = False

    def __init__( self, locust ):
        self.locust = locust

        # Figure out site and sandbox from URL
        host_segs = self.locust.host.split('//')[1].split('.')
        self.subdomain = host_segs[0]
        self.main_site = 'https://www.{}'.format( '.'.join( host_segs[1:] ) )
        print("=== Initializing %s in %s ===" % ( self.subdomain, self.main_site ))

    def create_site( self ):
        rv = False

        # Skip if the site is already created
        response = self.locust.get( self.locust.host )
        if not response.ok:

            # Create the new site
            self.locust.get( self.main_site, "ONBOARD PAGE" )
            response = self.locust.post( self.main_site + self.create_url, {
                'subdomain': self.subdomain,
                'sandbox_name': 'Load test {}'.format( self.subdomain ),
                'onboard_role': 'All',
                'email': self.locust.email,
                'password1': 'mptest1',
                'tzoffset': '',
                'start_trial': 'LoadTest',
                }, "CREATE SITE" )
            rv = response.ok

            print("CREATE SITE {} completed".format( self.subdomain ))
            self.site_created = rv

        return rv