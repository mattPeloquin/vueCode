#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Initialize Django (through settings) with config files
    and some environment variables.

    SECURE - Yaml is used for MPF config files, but only for standard
    data types (safe_load).

    Django settings are loaded here, so are not available and no important
    dependencies related to settings may be added.

    HACK - There are hard-coded name dependencies in this file.
"""
import os
import yaml
import json

from ..utils import safe_int
from ..utils.strings import bool_convert
from . import clean_env_get
from .paths import home_path
from .paths import mpframework_path
from .platforms import all_platforms


def get_ecs():
    """
    Factory for creation and caching config settings
    """
    global _ecs
    if not _ecs:
        _ecs = EnvConfigSettings()
    return _ecs
_ecs = None


def setup_env_config( argv=None, wsgi=False, profile=None ):
    """
    Setup settings and point Django at them, and do any fixup of profiles and
    command options based on command line arguments and defaults.

    MPF assumes settings for a deployment instance are driven from
    mpframework.settings, which pulls in other platform settings based
    on the MP_PLATFORMS environment variable.
    The settings here are done with environment variables and must be
    loaded before the Django settings process.
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mpframework.settings'

    # Since Django websever is not used in production, it is safe
    # to assume local as default case
    profile_name = profile
    if not profile_name:
        profile_name = clean_env_get('MP_PROFILE')
    if not profile_name:
        print("MP_PROFILE not found, setting to local")
        profile_name = 'local'
    print("# Environment: profile=%s, wsgi=%s" % (profile_name, wsgi))

    # Override the MP_PROFILE environment variable with current profile name
    # Only applies to this process
    os.environ['MP_PROFILE'] = str( profile_name )

    # Note whether Django is being run via WSGI or dev webserver
    # If neither of these are true, a command is being run
    devweb = bool(('runserver' in argv) or ('run_mpserver' in argv)) if argv else False
    assert( not(wsgi and devweb) )
    os.environ['MP_WSGI'] = str( wsgi )
    os.environ['MP_DEVWEB'] = str( devweb )
    os.environ['MP_COMMAND'] = str( not (devweb or wsgi) )


class EnvConfigSettings:
    """
    ECS - read environment settings from yaml configs or process environment

    Config values may come from shell environment variables or from a series of
    yaml config files, where config file naming convention supports
    overriding default files.

    Config files are assumed to be in:
     1) "mpFramework/settings/profiles"
     2) "/settings" for derived platforms defined in MP_PLATFORMS

    Files override each other, both in terms of profile naming (described below)
    and in terms of the MP_PLATFORMS entries, where the later items in
    the list override the earlier ones.
    By convention, the "root" for a given instance deployment is the last
    entry in MP_PLATFORMS. For a normal deployment, that platform
    entry would contain the AWS resource information for the deployment.

    The yaml config file naming is tied to the profile name present in the
    'MP_PROFILE' value, which may be set in the environment or passed to
    us on initialization.

    Using the profile name, config files are loaded based on:
     1) mpFramework settings and then derived platform settings (lms, root, etc.)
     2) First loading a file named "shared.yaml"
     3) Decomposing the profile name with dashes and looking for profile
        files based on each part of the name

    For example given, if MP_PROFILE is set to "local-prod" and
    MP_PLATFORMS is "mpextend", the following will be attempted:

        shared.yaml        (in mpframework/settings/profiles)
        shared.yaml        (in mpextend/settings)
        local.yaml         (first in mpframework, then in mpextend)
        local-prod.yaml     (first in mpframework, then in mpextend)
    """
    _PROFILE_FILE_SHARED = 'shared.yaml'
    _PROFILE_FOLDER_NAME = 'settings'
    _PROFILE_FOLDER_FRAMEWORK = mpframework_path( _PROFILE_FOLDER_NAME, 'profiles' )

    def __init__( self, profile=None ):
        self.info = safe_int( os.environ.get('MP_LOG_LEVEL_INFO_MIN', '2') ) > 1
        self.debug = os.environ.get('MP_FAB_LOG', False)

        # Setup config paths to look for files in by adding top-level platform folders
        # (assumption is each has a settings folder)
        self.config_paths = [ self._PROFILE_FOLDER_FRAMEWORK ]
        platforms = all_platforms()
        print("# PLATFORMS: %s" % platforms)
        for name in platforms:
            self.config_paths.append( home_path(name, self._PROFILE_FOLDER_NAME) )

        # Setup profile to run with
        if profile is None:
            self.settings_profile = clean_env_get('MP_PROFILE')
            if self.settings_profile is None:
                self.settings_profile = ''
        else:
            self.settings_profile = profile
        print("# PROFILE:  %s" % self.settings_profile)
        self._settings = self._load_profile()

    def load_value( self, key, default=None, required=False, echo=False, suppress=False ):
        """
        Load value from environment or the settings, with optional default
        and logging options.
        A json conversion is attempted on the value, to allow embedding json
        in environment variables to support dicts in the settings.
        """
        rv = default

        # If value is in environment variable, strip out any double quotes
        value = clean_env_get( key )
        if value:
            rv = value
            if not suppress and self.info:
                print("#   %s: %s  (env)" % (key, value))
        else:
            # Otherwise try to load from yaml config files
            try:
                value = self._settings[ key ]
                rv = value
            except KeyError:
                if required: print("# WARNING:  %s  NOT loaded" % key)
            if echo and self.info:
                print("#   %s: %s  (yaml)" % (key, rv))

        # Expand any embedded JSON
        if isinstance( rv, str ):
            try:
                rv = json.loads( rv )
            except Exception:
                pass

        return rv

    def load_bool( self, *args, **kwargs ):
        return bool_convert( self.load_value(*args, **kwargs) )

    def load_int( self, *args, **kwargs ):
        return int( self.load_value(*args, **kwargs) )

    def _load_profile( self ):
        """
        Load yaml files for a given profile name such as "dev-prod"

        Look in mpFramework and then platform folders
        Do shared file, and then split the profile name by dashes,
        trying to load each segment.

        Try to load config file(s) with the given name from our known
        config locations, if exists, add to dict, with later
        additions trumping earlier ones.

        Thus the convention of listing mpframework first in the platforms
        list and the root instance last allow platforms to override
        defaults, and platform root to override all.
        """
        profile = {}
        for path in self.config_paths:
            if self.debug: print("#   Loading profiles for: %s" % path)

            file_name = self._PROFILE_FILE_SHARED
            remaining_segments = self.settings_profile
            current_segments = None
            while True:

                file_config = self._load_config_file( path, file_name )
                if file_config:
                    # New profile yaml overwrites old while...
                    # ...MERGING KEYS for ONLY TOP-LEVEL DICT!!!
                    # Supports embedding application settings into nested dicts whose
                    # TOP LEVEL KEYS can be overridden
                    for key, value in file_config.items():
                        if isinstance( value, dict ):
                            new_dict = profile.get( key, {} )
                            new_dict.update( value )
                            value = new_dict
                        profile[ key ] = value

                # Shift right to next segment, end if done or add next segment to file_name
                next_segment, _, remaining_segments = remaining_segments.partition('-')
                if next_segment:
                    current_segments = current_segments + "-" + next_segment if current_segments else next_segment
                    file_name = "{}.yaml".format( current_segments )
                else:
                    break

        return profile

    def _load_config_file( self, path, name ):
        """
        Load config file into YAML with option to include yaml files from the
        same folder as the original.
        The config file may not exist, which is valid.
        """
        try:
            try:
                file_path = os.path.join( path, name )
                with open( file_path ) as config_file:
                    if self.debug: print("#     %s" % file_path)

                    config = yaml.safe_load( config_file )

            except IOError as e:
                if self.debug: print("#     %s" % e)
                return

            # Load (and overwrite) any includes
            includes = config.pop( 'YAML_INCLUDES', None )
            if includes:
                for include in includes:
                    with open( os.path.join(path, include) ) as include_file:
                        config.update( yaml.safe_load( include_file ) )

            return config

        except Exception:
            import traceback
            traceback.print_exc()
            raise
