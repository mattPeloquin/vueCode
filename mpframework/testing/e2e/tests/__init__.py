#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    E2E test cases

    NOTE - RELATIVE IMPORTS CANNOT BE USED IN TEST CASE MODULES
    due to the dynamic importing used here.
"""

__all__ = []

def load_e2e_test_cases( path, all ):
    """
    Load all System classes whose names start with MP_TEST_TYPE
    into a modules __all__ export.
    These are usually setup by SystemTestCase.register, and makes them
    available for execution via unittest.
    """
    if all:
        # Already loaded for this module
        return
    import pkgutil
    import inspect
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    for loader, mod_name, _is_pkg in pkgutil.walk_packages( path ):

        try:
            #print("  finding: %s -> %s" % ( path, mod_name))
            module = loader.find_module( mod_name ).load_module( mod_name )

            for name, value in inspect.getmembers( module ):

                # Add a system test class
                if name.startswith( settings.MP_TEST_TYPE ):
                    class_name = "{}_{}".format( name, mod_name )
                    print("LOADING: %s" % class_name)
                    globals()[ class_name ] = value
                    all.append( class_name )

        except ImproperlyConfigured :
            # Ignore warnings about settings
            pass

        except Exception as e:
            # Trying to load tests during inspection will raise exceptions about
            # settings config not being setup, which can be ignored
            print("LOAD EXCEPTION: %s -> %s" % (mod_name, e))
            import traceback
            traceback.print_exc()

load_e2e_test_cases( __path__, __all__ )
