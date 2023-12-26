#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric is for composing and delegating behavior; keep configuration in
    Django, environment, and profile settings.
    Fabric Tasks are defined under mpframework.deploy.fab and
    any extensions are under <package>.deploy.fab
"""

# Get the MPF fab tasks
from mpframework.deploy.fab.import_all import *

# Look for any extensions
from mpframework.common.deploy.platforms import specialization_platforms
for name in specialization_platforms():
    try:
        exec( "from {}.deploy.fab.import_all import *".format( name ) )
    except Exception as e:
        print( "\nERROR initializing fab tasks: %s\n %s\n" % (name, e) )
