#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    DESIGNED TO BE import * from the fabfile, only once per fab command

    This is separated out from the fabfile mainly to support running
    profiling in the imports.
"""

# Fabric does its own search for tasks in sub-modules; thus to avoid registering
# duplicates of tasks due to the way deploy.fab folders are organized,
# explicitly include each file here instead of just including deploy.fab

from .env import *
from .files import *
from .shell import *
from .djutils import *
from .composed import *
from .test import *
