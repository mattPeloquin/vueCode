#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Setup some global Fabric V1-like state to support defining
    hosts, profile, etc. once for a set of commands.

    ASSUMES PLATFORMS FOR LOCAL WILL MATCH REMOTE CALLS
"""

from mpframework.common.deploy.platforms import all_platforms
from mpframework.common.deploy.platforms import root_name


class V1Env:

    def __init__( self ):
        self.env_setup = False
        self.is_remote = False
        self.prod_warn = True

        # Assume fixed server user
        self.user = 'ec2-user'

        # Add support for multiple host IPs being defined at the
        # start of a command, which can then be iterated through
        self.hosts = []

        # Default profile commands will be run with
        # If empty uses environment settings (local or remote)
        self.profile = ''

        # MPF platforms commands will be run with, defaults to MP_PLATFORMS
        self.mp_platforms = all_platforms()
        self.root_name = root_name()

        # SSH file - assumes all servers in a command use same key
        self.keyfile = ''
        self.keyfile_path = ''

        # Environment variables passed to remote
        self.mp_env = {}

        # Logging for fabric and Python warnings
        self.fab_log = False
        self.warnings = False

        # Allow suppressing sudo in scripts
        self.mp_sudo_ok = True

        # Flag to prefix activate to all commands if bashrc not initialized
        self.add_venv_activate = False

v1env = V1Env()
