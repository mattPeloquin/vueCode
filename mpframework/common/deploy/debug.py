#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    General debugging support
"""
import os
import sys
from django.conf import settings

from .. import log
from ..logging.utils import remove_secrets
from .paths import home_path


def debug_toolbar_show( request ):
    """
    Callback for Django Debug Tool bar, controls urls it is shown on

    MPF controls loading of the toolbar for debug, so
    that is not checked and this is not called unless debug is active
    """
    if request.is_lite or request.is_api:
        return

    # Only show for internal IPs
    if request.ip in settings.INTERNAL_IPS:

        # Only use debug toolbar with specific screens
        return request.mppath.startswith( (
                    settings.MP_URL_USER,
                    settings.MP_URL_PUBLIC,
                    settings.MP_URL_PORTAL,
                    settings.MP_URL_STAFF_ADMIN,
                    ) )

#--------------------------------------------------------------------
# Cut/paste this line to set a pdb break point, or use pdb_stop

# import pdb; pdb.set_trace()

def pdb_stop():
    import pdb
    pdb.set_trace()


#--------------------------------------------------------------------

def get_settings_dict( include=None ):
    """
    Create display dictionary from settings with secrets removed
    and optional startswith include filter applied

    This should only be used in debug or with debugging
    """
    # Settings is a lazy dict, so enumerate it to turn into a real dict
    settings_dict = {}
    setting_names = settings.__dir__()
    for name in setting_names:
        settings_dict[name] = eval('settings.' + name)
    return remove_secrets( settings_dict, include )


#--------------------------------------------------------------------
#   Tracing, for targeted logging of code lines
#
#   Use frame tracing along with reading of code files to provide
#   log output of code lines as they are executed

file_line_cache = {}

def _read_lines(path):
    with open(path, 'r') as code_file:
        return code_file.readlines()

def _should_trace_path(path, root_folder, ignore=['.venv', 'log', 'cache']):
    return path.startswith(root_folder) and not any( name in path for name in ignore )

def _should_trace_line(line, ignore=['format']):
    return line and not any( name in line for name in ignore )

def _should_trace_call(call, ignore=['log']):
    return not any( name in call for name in ignore )

def trace_on( code_root=home_path() ):
    """
    Setup frame tracing designed to output lines of test cases
    """
    def _trace_on(frame, event, arg):
        #caller = frame.f_back
        line_no = frame.f_lineno
        routine_name = frame.f_code.co_name
        path = frame.f_code.co_filename
        folder, file = os.path.split(path)

        if 'line' == event:
            if _should_trace_path(path, code_root):
                lines = file_line_cache.setdefault(path, _read_lines(path))
                line = lines[line_no - 1].strip()
                if _should_trace_line(line):
                    log.debug2("%s(%s): %s", path[len(code_root):], line_no, line)
            return _trace_on

        if 'call' == event:
            if _should_trace_path(path, code_root) and _should_trace_call(routine_name):
                return _trace_on
    sys.settrace(_trace_on)

def trace_off():
    def _trace_off(frame, event, arg):
        return
    sys.settrace(_trace_off)
