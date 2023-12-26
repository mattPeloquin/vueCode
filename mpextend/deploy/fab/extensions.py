#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity shell extensions
"""

from mpframework.deploy.fab.utils import runcmd
from mpframework.deploy.fab.utils import home_folder


def mpextend_update_pip( c ):
    """
    Add mpExtend specific pip items
    """

    runcmd( c, [ 'pip install --upgrade -r',
            home_folder( 'mpextend', 'deploy', 'pip_shared.txt' ) ] )
