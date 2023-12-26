#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity-specific tasks
"""

from mpframework.deploy.fab.env import set_env
from mpframework.deploy.fab.utils import runcmd


DEFAULT_IAM_PROFILE = 'vueocity'


def runaws( c, command, iam=None, **kwargs ):
    """
    Run an AWS CLI command using the given IAM profile
    """
    set_env( AWS_PROFILE=iam if iam else DEFAULT_IAM_PROFILE )

    return runcmd( c, command, **kwargs )
