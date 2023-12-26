#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for ops related urls
"""
from django import forms
from django.conf import settings
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common import constants as mc
from mpframework.common.ip_throttle import ban_ip
from mpframework.common.ip_throttle import banned_ips
from mpframework.common.aws.ec2 import get_ec2_instances
from mpframework.common.view import root_only
from mpframework.common.tasks.bots import start_bots
from mpframework.common.tasks.bots import stop_bots


class _BanForm( forms.Form ):
    ip = forms.CharField( required=False, label="IP to ban" )
    seconds = forms.IntegerField( required=False, label="Seconds" )
    banned_ips = forms.CharField( required=False,
                widget=forms.Textarea( attrs=dict( mc.UI_TEXTAREA_LARGE, **{
                    'readonly': True,
                    }) ),
                label="Banned IPs" )
    throttle_period = forms.IntegerField( required=False,
                label="Throttle count period in seconds")
    throttle_thresh = forms.IntegerField( required=False,
                label="Hits from an IP in period to trigger throttle (0 for no throttle)")
    throttle_thresh_boost = forms.IntegerField( required=False,
                label="Extra hits added to expensive endpoints")
    warn_seconds = forms.IntegerField( required=False,
                label="Number of seconds warning ban lasts")
    ban_threshold = forms.IntegerField( required=False,
                label="Number of warnings bans before long ban")
    ban_seconds = forms.IntegerField( required=False,
                label="Number of seconds long ban lasts")
    throttle_exempt = forms.CharField( required=False,
                widget=forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
                label="IPs exempt from throttle")

# For convenience, define the items in the form, and then use their
# name and prefix to match up to the global option functions
class _TuningForm( forms.Form ):

    disable_non_critical = forms.BooleanField( required=False,
                label="Disable non-critical processing")

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Add dynamic integer values from settions
        for option in settings.MP_OPTIONS:
            if len( option ) > 2:
                self.fields[ option[0] ] = forms.IntegerField( required=False,
                            label=option[2] )

@root_only
def dashboard( request ):

    # Ban form
    if 'ban' in request.POST:
        bform = _BanForm( request.POST )
        if bform.is_valid():
            ban_ip( bform.cleaned_data.get('ip'),
                    bform.cleaned_data.get('seconds') )
            sys_options.update_options( bform.cleaned_data )
    bdata = _initial_data( _BanForm )
    bdata.update({ 'banned_ips': banned_ips() })
    bform = _BanForm( bdata )

    # System tuning form
    if 'tuning' in request.POST:
        tform = _TuningForm( request.POST )
        if tform.is_valid():
            sys_options.update_options( tform.cleaned_data )
    tform = _TuningForm( _initial_data(_TuningForm) )

    # Bot management
    if 'bots_start' in request.POST:
        start_bots()
    if 'bots_stop' in request.POST:
        stop_bots()

    # Convert Boto items into a simpler server info dict
    servers = {}
    if settings.MP_CLOUD:
        for instance in get_ec2_instances():
            try:
                server_info = {}
                server_info['name'] = instance.tags.get('Name')
                server_info['id'] = instance.pk
                server_info['itype'] = instance.get_attribute('instanceType').get('instanceType')
                server_info['state'] = instance.state
                server_info['ip'] = instance.ip_address
                server_info['dns'] = instance.public_dns_name
                server_info['private_dns'] = instance.private_dns_name
                server_info['launch_time'] = instance.launch_time
                servers[ instance.private_ip_address ] = server_info
            except Exception as e:
                log.info("Error reading server info: %s", e)

    return TemplateResponse( request, 'root/ops/dashboard.html', {
                'ban_form': bform,
                'tuning_form': tform,
                'root_policy': dict( sys_options.root().policy ),
                'using_aws': settings.MP_CLOUD,
                'server_ip': settings.MP_IP_PRIVATE,
                'servers_info': servers,
                 })


def _initial_data( Form ):
    # Load any initial data from system option fields in form class
    rv = {}
    for field_name in Form().fields:
        sys_field = getattr( sys_options, field_name, None )
        if sys_field:
            rv[ field_name ] = sys_field()
    return rv
