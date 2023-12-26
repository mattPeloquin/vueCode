#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric tasks and support related to automated testing
"""
import sys
import io
from importlib.util import find_spec

from mpframework.common.deploy.platforms import all_platforms

from .v1env import v1env
from .env import set_env
from .decorators import mptask
from .decorators import elapsed_time
from .utils import home_folder
from .utils import framework_folder
from .utils import target_path_join
from .utils import runcmd
from .utils import rundj


_playpen_initialized = False


@mptask
@elapsed_time
def test( c, test=None, level='0', db=False ):
    """fab test [ -t xyz --level 1 --db ]"""
    _test_unit( c, test, level=level, db=db )

@mptask
def test_e2e( c, test=None ):
    """Selenium tests using self-contained local server"""
    _test_e2e( c, 'SystemInternalTests', test )

@mptask
def test_live( c, url, test=None, site='_new_test_site' ):
    """Selenium live: url [ -t xyz --site abc ]"""
    set_env( MP_TEST_URL=url )
    _test_e2e( c, 'SystemExternalTests', test, site=site )

@mptask
def test_local( c, test=None, site='', url='http://localhost' ):
    """Selenium localhost: [ -t xyz --site abc --url xyz.com ]"""
    test_live( c, url, test, site )

@mptask
def test_load( c, test='default', site=None ):
    """Load test (requires locust): [ -t xyz --site abc ]"""
    print("\nOpen browser to http://localhost:8089 to start test...\n")
    cmd = [ 'locust -f mpframework/testing/load/{}.py'.format( test ) ]
    site and cmd.append('--host="https://{}"'.format( site ))
    runcmd( c, cmd )

#--------------------------------------------------------------------

def _test_setup( c, kwargs ):
    """
    Shared setup code for processing test options
    """
    set_env( MP_LOAD_ADMIN='True' )
    set_env( MP_TEST_LEVEL=kwargs.pop('level', '0') )
    db = '1' if kwargs.pop( 'db', None ) else '0'
    set_env( MP_TEST_USE_NORMAL_DB=db )
    if( kwargs.pop( 'init', False ) ):
        _setup_playpen_files( c )

def _test_unit( c, test_name, **kwargs ):
    """
    Shared unit test launch code
    """
    _test_setup( c, kwargs )
    # HACK - if specific test name(s) provided run them
    if test_name:
        if '.' in test_name:
            return _run_djtest( c, 'Specific', test_name, **kwargs )
        elif test_name in ['Model', 'View']:
            return _run_djtest( c, test_name, '', **kwargs )
    # Otherwise run all non-selenium
    _test_common( c )
    if( _run_djtest( c, 'Model', '', **kwargs ) ):
        if( _run_djtest( c, 'View', '', **kwargs ) ):
            test_static( c )

def _test_e2e( c, test_type, test_name, **kwargs ):
    """
    Shared code for Selenium tests
    e2e test naming is special cased; if name not provided, run basic smoke
    """
    _test_setup( c, kwargs )
    set_env( MP_TEST_SITE_NAME=kwargs.pop('site', '') )
    set_env( MP_TEST_WAIT=kwargs.pop('wait', '0') )
    set_env( MP_TEST_RUNS=kwargs.pop('runs', '10') )
    set_env( MP_TEST_BROWSER=kwargs.pop('browser', 'chrome') )
    test_name = test_name or 'smoke.basic'
    _run_djtest( c, test_type, test_name, **kwargs )

def _setup_playpen_files( c ):
    """
    When profile expects compressed static files, need to ensure they
    are in place for the test playpen
    """
    global _playpen_initialized
    if not _playpen_initialized:
        from .djutils import static
        set_env( MP_TESTING='True' )
        static( c )
        _playpen_initialized = True

def _test_common( c ):
    """
    mpframework.common tests, outside Django
    """
    runcmd( c, [ 'python ' + framework_folder( 'common', 'tests.py' ) ])

def _run_djtest( c, test_type, test_name, **kwargs ):
    """
    Execute dj command to run tests for ONE MP_TEST_TYPE.
    Returns None if a test fails.
    """
    set_env( MP_TESTING='True' )
    cmd = 'test --traceback'

    parallel = kwargs.pop( 'parallel', None )
    if parallel:
        cmd = '{} --parallel {}'.format( cmd, parallel )
    keep_db = kwargs.pop( 'keepdb', None )
    if keep_db:
        cmd = '{} --keepdb'.format( cmd )

    test_type, tests = _fixup_dj_tests( test_type, test_name )
    set_env( MP_TEST_TYPE=test_type )
    for t in tests:
        try:
            failure = rundj( c, cmd, t, **kwargs )
            if failure:
                print("FAIL %s, return code: %s" % (t, failure))
                return
        except Exception as e:
            print("ERROR %s: %s" % (t, e))
            raise
    return True

def _fixup_dj_tests( test_type, test_name ):
    """
    HACK - MPF test classes use naming conventions to define model, view,
    and system tests based on classes in test modules with classes:

        'ModelTests', 'ViewTests',
        'SystemInternalTests', 'SystemExternalTests'

    Usually tests are run by specifying default, app or system test name

        fab test
        fab test-model mpcontent

    A non-System test name can also be passed in with dot format, in which
    case it is interpreted as a fully formed name, e.g.:

        fab test-model mpframework.content.mpcontent.ModelTests.test_category

    """
    # Determine specific model or view test type from name
    if test_type == 'Specific':
        test_type = 'View' if 'View' in test_name else 'Model'
    e2e_test = test_type.startswith('System')

    if test_name:
        # Test names were passed in
        test_names = [ test_name ]
    else:
        # Get the test to run from yaml profile config
        # HACK -- Reading from LOCAL profile, which could be out of sync with server
        # Note this causes the settings process to be run once before the test run begins
        from mpframework.settings import MP_TEST_DJTESTS
        test_names = MP_TEST_DJTESTS

    test_names = list( dict.fromkeys( test_names ).keys() )

    print("Looking for tests: %s -> %s" % (test_type, test_names))
    full_test_names = []
    test_text = test_type + 'Tests'
    for test_name in test_names:

        # If not system and path in name, assume full name requested
        if not e2e_test and test_name.count('.') > 1:
           full_test_names.append( test_name )

        # For other cases, assume MPF conventions, adding tests
        # with the given name for every platform where they exists
        else:
            for platform in all_platforms():
                #print("  checking: %s for %s" % (platform, test_name))
                test_method = None

                # Map onto MPF tests module folder conventions for e2e
                # and unit tests under service group folders
                if e2e_test:
                    test_module = [ platform, 'testing', 'e2e', 'tests' ]
                    if test_name:
                        names = test_name.split('.')
                        if names[-1].startswith('test_'):
                            test_method = names[-1]
                            del names[-1]
                        test_module += names + [ test_type ]
                else:
                    test_module = [ platform, test_name, 'tests' ]

                test_module = '.'.join( test_module )

                # Verify the module and sort-of verify the test exists by checking
                # if the type name appears in source file
                #print("Importing: %s" % test_module)
                add = False
                try:
                    spec = find_spec( test_module )
                    if spec:
                        with open( spec.origin ) as file:
                            if test_text in file.read():
                                add = True
                            else:
                                v1env.fab_log and print("No test in: %s" % test_module )
                    else:
                        v1env.fab_log and print("No module for: %s" % test_module )
                except ( ImportError, AttributeError ) as e:
                    v1env.fab_log and print("Can't find module: %s -> %s" %
                                (test_module, e))
                except Exception as e:
                    # If a module fails due to dependencies on settings, add it
                    v1env.fab_log and print("ERROR inspecting test module: %s -> %s %s" %
                                (test_module, type(e), e ))
                    add = True
                if add:
                    if e2e_test:
                        if test_method:
                            test_module = '.'.join([ test_module, test_method ])
                    # When type and name is specified, add the 'XyzTests' class name,
                    # otherwise just pass on to test runnner
                    elif test_type and test_name:
                        test_module = test_module + '.' + test_type + 'Tests'

                    #print("Adding test module: %s" % test_module)
                    full_test_names.append( test_module )

    full_test_names = tuple( full_test_names )
    if full_test_names:
        print("  %s\n" % '\n  '.join( full_test_names ))
    return test_type, full_test_names

#--------------------------------------------------------------------

@mptask
def test_static( c, all=False, init=False, warn=False ):
    """
    Run pyflakes static analysis (local only)
    pyFlakes Chosen as quickest, least noisy static check; only care about
    real errors vs. style check stuff
    This doesn't really need to be run remotely and it is easiest to
    manipulate output with local python, so skip on remote calls
    """
    if v1env.is_remote:
        print( "\nSkipping static analysis for remote machine" )
        return

    if all: warn = init = True
    init_only = [] if init else [ '__init__', 'import *', 'star imports' ]
    warn_only = [] if warn else [ 'imported but unused', "'_' is assigned" ]

    for platform in all_platforms():
        folder = home_folder( platform )
        print( "------- PyFlakes: %s --------" % folder )
        out_folder = home_folder('.work')
        init_filename = target_path_join( out_folder, platform + '_warnings__init__.txt')
        warning_filename = target_path_join( out_folder, platform + '_warnings.txt')
        error_filename = target_path_join( out_folder, platform + '_errors.txt')
        try:
            ioout = io.StringIO()
            runcmd( c, ['pyflakes ' + folder], out_stream=ioout, warn=True )
            ioout.seek(0)

            with open( target_path_join( folder, init_filename ), 'w' ) as init_file, \
                    open( target_path_join( folder, warning_filename ), 'w' ) as warnings_file, \
                    open( target_path_join( folder, error_filename ), 'w' ) as error_file:
                for line in ioout.readlines():
                    if any( s in line for s in init_only ):
                        init_file.write( line )
                    elif any( warning in line for warning in warn_only ):
                        warnings_file.write( line )
                    else:
                        error_file.write( line )
                        sys.stdout.write( line )

        except Exception as e:
            print( "pyflakes exception: %s %s" % ( type(e), e ) )
    sys.stdout.flush()
    print( "-" * 50 )
