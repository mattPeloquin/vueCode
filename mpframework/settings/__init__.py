#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Load MPF Django settings for mpframework and extension platforms.
"""

# Import settings into the locals namespace, so Django adds to settings
try:

    # Get values from local config or environment variables
    from .env import *

    # Load mpFramework modules that add items directly to Django settings
    from ._first import *
    from ._db import *
    from ._cache import *
    from ._file import *
    from ._template import *
    from ._misc import *
    from ._dev import *

    """
    Load settings for specialization platforms
    Settings files are loaded into the current scope, this is additive and
    will override settings values that came before.
    """
    from mpframework.common.deploy.platforms import specialization_platforms
    for name in specialization_platforms():
        try:
            # Passes globals() as local to exec as locals to add variables
            # to the globals scope which is what Django settings expects.
            exec( "from {}.settings import *".format( name ), {}, globals() )

        except Exception as e:
            print( "\nERROR initializing settings: %s\n %s\n" % (name, e) )
            raise

except Exception:
    import traceback
    traceback.print_exc()
    raise
