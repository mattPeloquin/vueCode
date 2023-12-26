#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Default load test entry point, creates a new account
    and exercises with default data
"""

# Fixup the sys path so this file can import MPF modules correctly
from os import sys, path
load_path = path.dirname( __file__ )
framework_path = path.abspath( path.join( load_path, '..', '..', '..') )
sys.path[0] = path.abspath( load_path )
sys.path.append( path.abspath( framework_path ) )

from locust import TaskSet
from locust import task

from django.utils.crypto import get_random_string

from blocks.user import UserLocust
from blocks.site import TestSite


class DefaultLoadTasks( TaskSet ):
    site = None

    def on_start( self ):
        self.site = TestSite( self.locust )
        self.site.create_site()
        self.locust.new_user()

    @task(4)
    def load_portal( self ):
        self.locust.load_portal()

    @task(6)
    def access_content( self ):
        self.locust.access_item()
    @task(8)
    def content_state( self ):
        self.locust.send_current_item_state()

    @task(1)
    def user_history( self ):
        self.locust.get( '/user/uc/user_usage', "HISTORY" )
    @task(1)
    def user_profile( self ):
        self.locust.get( '/user/', "PROFILE" )
    @task(1)
    def user_account( self ):
        self.locust.get( '/bh/user/account', "ACCOUNT" )


class WebsiteUser( UserLocust ):
    task_set = DefaultLoadTasks
    min_wait = 200
    max_wait = 8000

    # This is overridden if a host provided on command line
    host = 'https://{}.vueocity.com'.format( get_random_string( 4, 'mpl-' ).lower() )
