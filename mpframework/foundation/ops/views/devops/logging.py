#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manage logging options
"""
from django import forms
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe

from mpframework.common import sys_options
from mpframework.common.view import root_only

from ...process_update import update_processes_for_workfn


class _LogOptions( forms.Form ):

    logging_info = forms.IntegerField( required=False, label=mark_safe(
            "INFO: 0 is warning/errors only; 1-4 add verbosity<br>"
            "1-2 shown when debug=1; 3 when debug=2, etc." ))
    log_timing = forms.BooleanField( required=False, label="Extra timings" )
    logging_debug = forms.IntegerField( required=False, label=mark_safe(
            "DEBUG: >= 1 enables debug logging; 2, 3, 4 add verbosity<br>"
            "Adds some overhead, enables the logging areas below" ))
    log_cache = forms.BooleanField( required=False, label="Cache set/get/invalidate" )
    log_db = forms.BooleanField( required=False, label="DB SQL statements" )
    log_detail = forms.BooleanField( required=False, label="Misc details" )
    log_external = forms.BooleanField( required=False, label="External logging AWS, Selenium, Boto, etc." )
    logging_verbose = forms.BooleanField( required=False, label="Use verbose logging string" )
    logging_values = forms.BooleanField( required=False, label=
                "Display value dumps (may cause side effects like extra DB queries)" )

@root_only
def logging( request ):
    """
    Update logging options

    Note that even though the option values in the DB are always updated in this
    view, the process_update mechanism is used to get other processes to read the
    option changes the next time they do a process_update poll
    """
    if 'POST' == request.method:
        form = _LogOptions( request.POST, auto_id='debug_%s' )
        if form.is_valid():
            # Set options at requested level
            sys_options.update_options( form.cleaned_data )
            update_processes_for_workfn('set_logging')
    else:
        initial_data = {
            'logging_info': sys_options.logging_info(),
            'logging_debug': sys_options.logging_debug(),
            'log_timing': sys_options.log_timing(),
            'log_cache': sys_options.log_cache(),
            'log_db': sys_options.log_db(),
            'log_detail': sys_options.log_detail(),
            'log_external': sys_options.log_external(),
            'logging_verbose': sys_options.logging_verbose(),
            'logging_values': sys_options.logging_values(),
            }
        form = _LogOptions( initial_data, auto_id='debug_%s' )

    return TemplateResponse(request, 'root/ops/logging.html', {
                'form': form,
                })
