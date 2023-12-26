#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Elastic Load Balancers (ELB)
    MPF only uses application ELBs, (known as both ALBs or ELBs)

    This code is for creating and managing them and the target groups that
    collect servers together for assigning to ELB listeners (public endpoints).
"""
from django.conf import settings

from .. import log
from .utils import validate_response
from . import get_client


def get_elb():
    return get_client('elbv2')

def add_instance():
    elb = get_elb()
    arn = get_target_group_arn()
    instance = settings.MP_AWS_INSTANCE['id']
    log.info("Adding instance: %s -> %s", instance, arn)
    response = elb.register_targets( TargetGroupArn=arn,
                Targets=[{ 'Id': instance }] )
    validate_response( response )

def remove_instance():
    elb = get_elb()
    arn = get_target_group_arn()
    instance = settings.MP_AWS_INSTANCE['id']
    log.info("Removing instance: %s -> %s", instance, arn)
    response = elb.deregister_targets( TargetGroupArn=arn,
                Targets=[{ 'Id': instance }] )
    validate_response( response )

def get_target_group_arn():
    """
    Each profile can associate with one target group
    """
    elb = get_elb()
    name = settings.MP_ROOT_AWS['ELB_TARGET_GROUP']
    log.info2("Getting target group: %s", name)

    tgs = elb.describe_target_groups( Names=[ name ] )

    # There should only be one group
    return tgs['TargetGroups'][0]['TargetGroupArn']
