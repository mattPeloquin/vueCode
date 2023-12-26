#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for EC2 autoscale commands
"""
from django.conf import settings

from .. import log
from . import get_client
from .ec2 import get_ec2_instances


def get_autoscale( *args ):
    try:
        return mpAutoscale( *args )
    except Exception as e:
        log.info("Autoscale Error:\n%s", e )

def log_asg_info( detailed=False ):
    """
    Write current ASG state to log
    """
    client = get_client('autoscaling')
    for group in client.describe_auto_scaling_groups()['AutoScalingGroups']:
        log.info("  %s" % group.get('AutoScalingGroupName'))
        if detailed:
            log.info("\n  %s" % group)

class mpAutoscale:

    def __init__( self, profile, tag='', **kwargs ):
        """
        Create in preparation of starting an ASG, or access an exist one
        """
        self.client = get_client('autoscaling')
        self.profile_name = profile
        self.tag = tag
        self.full_name = '{}{}'.format( profile, tag )
        self.elbs = []

        # Setup options from command line
        self.code_rev = kwargs.pop('rev', '')

        # Try to map object onto existing ASG
        try:
            self._update()
        except Exception:
            log.exception("mpAutoscale create: %s", self.full_name)
            raise
        log.debug("New mpAutoscale object: %s, %s", self.client, self.full_name)

    def get_instances( self ):
        """
        Get instance information for the group. AWS doesn't store stuff we
        care about like IP with the group, so we have to query IDs and then
        go after in the info for each instance.
        """
        self._update()
        if self.asg:
            ids = [ i['InstanceId'] for i in self.asg['Instances'] ]
            if ids:
                instances = get_ec2_instances( ids=ids )
                if instances:
                    return instances
        return []

    def get_public_ips( self ):
        return [ instance.public_ip_address for instance in
                    self.get_instances() ]

    def _update( self ):
        """
        The only way to get up-to-date AS cluster info is from the client.
        Note that if it doesn't exist, it is a valid state for the object.
        """
        try:
            self.asg = self.client.describe_auto_scaling_groups(
                        AutoScalingGroupNames=[self.full_name]
                        )['AutoScalingGroups'][0]
        except IndexError:
            log.debug2("   Autoscale group did not exist: %s", self.full_name)
            self.asg = None
        try:
            self.lc = self.client.describe_launch_configurations(
                        LaunchConfigurationNames=[self.full_name]
                        )['LaunchConfigurations'][0]
        except IndexError:
            log.debug2("   LaunchConfig group did not exist: %s", self.full_name)
            self.lc = None
