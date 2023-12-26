#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric tasks that execute Django management commands
    on the target server
"""
import os
import re

from .env import set_env
from .utils import rundj
from .utils import on_windows
from .decorators import mptask
from .decorators import runs_once
from .decorators import prod_warn
from .decorators import skip_dev
from .decorators import code_current


#--------------------------------------------------------------------
# Tasks run locally on each server

@mptask
@prod_warn
@code_current
def static( c ):
    """
    Transpile, compress and deploy static files
    MUST be run if compress is on and code is updated, as the compress
    code uses the build number for versioning compiled files.
    Must be run for every server to setup offline manifest
    """
    set_env( MP_LOAD_ADMIN='True' )

    # Template and Sass compile generates lots of errors from base templates,
    # so turn down verbosity
    rundj( c, 'static_prepare --verbosity=0' )

    # Run compression and create offline manifest
    rundj( c, 'static_compress --verbosity=1' )

    # Move static files to serving location
    # The local static .work location holds files served during debug, but is
    # also used as the staging area for production transpile/compress,
    rundj( c, 'static_collect --noinput' )

@mptask
@skip_dev
def server_config( c, full=False ):
    """Create nginx, uwsgi, and server config files from settings"""
    if full:
        rundj( c, 'config_server', sudo=True )
    rundj( c, 'config_framework' )

@mptask
def aws_elb_add( c ):
    """Join profile's target group"""
    rundj( c, 'aws_elb --add' )

@mptask
def aws_elb_remove( c ):
    """Leave profile's target group"""
    rundj( c, 'aws_elb --remove' )

#--------------------------------------------------------------------
# DB tasks -- run once if multiple instances

@mptask
@prod_warn
@runs_once
def db_migrate( c ):
    """
    Run Django migrate
    """
    set_env( MP_LOAD_ADMIN='True' )
    rundj( c, 'db_migrate' )

@mptask
@prod_warn
@runs_once
def db_sync( c ):
    """
    Emulate pre-migrate db-sync (creates new app tables)
    """
    set_env( MP_LOAD_ADMIN='True' )
    rundj( c, 'db_migrate', '--noinput', '--run-syncdb' )

@mptask
@prod_warn
@runs_once
def db_load( c ):
    """
    DEV - Load fixtures (profile/platform defaults if blank)
    Not using Django's initial_data fixtures
    """
    rundj( c, 'db_load' )

@mptask
@runs_once
def db_shell( c, db='default' ):
    """Access mySql shell from a server, db=name"""
    rundj( c, 'db_shell --db {}'.format( db ), pty=True )

@mptask
def db_diff( c, min=False, all=False ):
    """
    Show ALTER TABLE SQL for model vs DB
    Some spurious messages are filtered by default
    """
    set_env( MP_LOAD_ADMIN='True' )
    result = rundj( c, 'sqldiff', '-a', '-d', hide=True, warn=True )
    skip_tests = [
        lambda txt: txt.find('MODIFY') > 0 and txt.find('AUTO_INCREMENT') > 0,
        lambda txt: min and txt.find('MODIFY') > 0 and txt.find('varchar') > 0,
        lambda txt: min and txt.find('MODIFY') > 0 and txt.find('NOT NULL') > 0,
        ]
    ansi_escape = re.compile(r'\x1b[^m]*m')
    for line in str(result).split( os.linesep ):
        test_line = ansi_escape.sub('', line)
        if all or not any( skip( test_line ) for skip in skip_tests ):
            if on_windows():
                print( test_line )
            else:
                print( line )

@mptask
@runs_once
def db_sql( c, app ):
    """Show SQL CREATE for specific apps"""
    rundj( c, 'sqlmigrate', app )

#--------------------------------------------------------------------
# Dev tasks

@mptask
def show_settings( c ):
    """Show all settings current profile would be run under"""
    rundj( c, 'show_settings' )
