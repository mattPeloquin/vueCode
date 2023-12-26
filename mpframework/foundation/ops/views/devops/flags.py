#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manage feature flags

    MPF feature flags use the sys_options for easy checking in code,
    which can be set at the system level and overridden at the site level.

    Feature flag forms use Boolean for any values under sys_options.flags() -
    so for values to show on form they must be added to system flags either
    through option defaults or editing the YAML in root sandbox.

    As with sys_options, system flags follow playpen scope, while
    site flags are global in scope (i.e., no playpen namespace is added).
"""
from django import forms
from django.template.response import TemplateResponse

from mpframework.common import sys_options
from mpframework.common.view import root_only


class _Flags( forms.Form ):
    """
    Setup fields based on the registered system flags
    """
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        for name in sys_options.flags().keys():
            self.fields[ name ] = forms.BooleanField( required=False, label=name )

@root_only
def system_flags( request ):
    """
    System flags reflect and update the root flags directly
    """
    if 'POST' == request.method:
        form = _Flags( request.POST, auto_id='flag_%s' )
        if form.is_valid():
            sys_options.update_options({ 'flags': form.cleaned_data })
    else:
        form = _Flags( sys_options.flags(), auto_id='flag_%s' )

    return TemplateResponse(request, 'root/ops/flags.html', {
                'form': form,
                'flag_scope': "System",
                })

@root_only
def sandbox_flags( request ):
    """
    Sandbox flags can optionally override root system flags, but only
    for system flags that are present.
    """
    sandbox = request.sandbox
    if 'POST' == request.method:
        form = _Flags( request.POST, auto_id='flag_%s' )
        if form.is_valid():
            flags = {}
            sys_flags = sys_options.flags()
            for name, sys_value in sys_flags.items():
                # Write items into sandbox that vary from system
                # POST doesn't send empty checkback values, so assume False
                value = form.cleaned_data[ name ]
                if value != sys_value:
                    flags[ name ] = value
            sandbox._policy.pop('flags')
            sandbox._policy['flags'] = flags
            sandbox.save()
    else:
        initial_data = {}
        for name, value in sys_options.flags().items():
            initial_data[ name ] = sandbox.flag( name )
        form = _Flags( initial_data, auto_id='flag_%s' )

    return TemplateResponse( request, 'root/ops/flags.html', {
                'form': form,
                'flag_scope': "Site",
                })
