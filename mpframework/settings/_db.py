#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Database setup

    DESIGNED TO BE * IMPORTED BY settings.__init__.py

    Create DB names based on configuration and server information
    to allow for sharing of same DB platform during development.

    DB connection management

    Available DB connections are often a bottleneck, especially for various
    RDS configurations. Opening connections too often is expensive.
    Django checks CONN_MAX_AGE at start and end of requests for each thread.
    MPF adds checking expiration at the end of spooler processing
    and uses non-shared connections for any other thread DB access.

    Ultimately for loaded servers must assume there will be a 1:1 match between
    threads and connections.

    MPF is instrumented to use a read replica DB endpoint. This is a
    separate Django DB and can support scaling out DB read replicas
    However, it also increases the open connections held by a Django thread,
    so when a read replica is not in use (e.g., AWS serverless scaling)
    it makes more sense to avoid the extra connections.
"""
import os

from mpframework.common.aws.secrets import aws_db_credentials
from mpframework.common.db.router import DbRouter
from mpframework.common.deploy.paths import work_path

from . import env

# Load the router explicitly here vs. pass string for lazy load, as
# import problems occurred running under spooler
DATABASE_ROUTERS = [ DbRouter() ]

# RDS mySQL / Auroa
if env.MP_CLOUD:

    _db_engine = 'django.db.backends.mysql'
    _db_host_default = env.MP_ROOT['DB']['MAIN_HOST']
    _db_host_read = env.MP_ROOT['DB']['MAIN_READ'] or _db_host_default

    # To allow co-habitation of logical DBs on a DB server, use playpen on DB name
    # Clean DB name to make sure mySQL is happy with it
    _db_name = env.MP_PLAYPEN.translate( str.maketrans('.-', '__') )

# Otherwise SQLite, map all DBs onto local
else:
    _db_engine = 'django.db.backends.sqlite3'
    _db_host_default = 'local'
    _db_host_read = 'local'
    # DB name reflects current profile and platform set, to allow
    # different dev configurations to be tested without stepping on each others data
    _db_name = work_path( "DB-{}.sqlite".format( env.MP_PLAYPEN_GROUP ) )

# Note if the DB read replica should be aliased to default
MP_DB_READ_REPLICA = _db_host_read != _db_host_default

if env.MP_CLOUD and env.MP_AWS_REMOTE_ONLY:
    # Prevent attempts to connect to DB if running AWS commands remotely
    DATABASES = {}
else:

    # Load DB info for dev and prod
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'HOST': _db_host_default,
            'NAME': _db_name,
            'CONN_MAX_AGE': env.MP_SERVER['DB_CONNECTION_AGE'],
            },
        }
    if MP_DB_READ_REPLICA:
        DATABASES['read_replica'] = {
            'ENGINE': _db_engine,
            'HOST': _db_host_read,
            'NAME': _db_name,
            'CONN_MAX_AGE': env.MP_SERVER['DB_READ_CONNECTION_AGE'],
            'TEST':  {
                'MIRROR': 'default',
                },
            }

    # Add auxilary DB if defined (for backup tasks, maintenance)
    if env.MP_ROOT['DB'].get('AUX_HOST'):
        DATABASES['aux'] = {
            'ENGINE': _db_engine,
            'HOST': env.MP_ROOT['DB']['AUX_HOST'],
            'NAME': env.MP_ROOT['DB'].get( 'AUX_NAME', _db_name ),
            }

    # Add credentials if AWS DB is used
    if env.MP_CLOUD:
        user, pwd = aws_db_credentials()
        for name in DATABASES:
            DATABASES[ name ]['USER'] = user
            DATABASES[ name ]['PASSWORD'] = pwd

"""--------------------------------------------------------------------
    Testing DB Support

    Django normally runs its tests with in-memory Sqllite DB.
    This is MPF default, as it is fast and tests most functionality.
    Tests are also supported with on-disk SQLLite because some testing
    cannot use in-memory SQLLite (e.g., threading) -- but on-disk is slower
    Also support testing with mySQL server/RDS to flush out any issues
    specific to mySQL support.
"""
if env.MP_TESTING:
    if env.MP_TEST_USE_NORMAL_DB:

        # Setting TEST.NAME value tells Django not to use in-memory Sqlite
        DATABASES['default']['TEST'] = { 'NAME': DATABASES['default']['NAME'] }

        if DATABASES['default']['HOST'] != 'MP_TBX':

            # On windows, when on-disk DB is used in testing, the sqllite file may
            # not be cleaned up, so blow it away
            # Need to do this ONCE, before Django starts trying to access test db
            if 'sqlite' in DATABASES['default']['ENGINE']:
                try:
                    os.remove( DATABASES['default']['TEST'] )
                except Exception:
                    pass

            # Make sure the DB exists on the mySQL target, as Django doesn't
            # create mySQL DBs as part of sync process
            elif 'mysql' in DATABASES['default']['ENGINE']:
                from mpframework.common.db.mysql import create_mysql_db
                create_mysql_db( DATABASES['default'] )

    else:
        # Force no read replica to get around problem with SqlLite
        # in-memory DBs not actually being shared by TEST.MIRROR setting
        MP_DB_READ_REPLICA = False
