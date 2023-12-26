#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared EC2 code
"""
import yaml
import requests

from ..deploy.paths import home_path
from . import get_resource


def get_ec2_instances( ids=None ):
    """
    Returns a list of instances associated with the current connection
    """
    resource = get_resource('ec2')
    return [ i for i in resource.instances.all() if
                ( ids is None or i.id in ids ) ]


# Cache info, which won't change while running
_INFO = {}

def aws_instance_info():
    """
    Get AWS _INFO for programmatic access from the EC2 instance's metadata,
    or from local secrets in case of local dev.
    """
    global _INFO
    if _INFO:
        return _INFO
    try:

        # Try reading local file
        # Can be used for dev cases, should not be used for production
        with open( home_path( '.secrets', 'aws.yaml' ) ) as aws_file:
            aws = yaml.safe_load( aws_file )
            _INFO = aws['INFO']
            _INFO['outside_aws'] = True

    except IOError:
        # Get EC2 info from the local location
        document = requests.get(
            'http://169.254.169.254/latest/dynamic/instance-identity/document',
            timeout=2 ).json()
        _INFO = {
            'outside_aws': False,
            'region': document['region'],
            'account': document['accountId'],
            'id': document['instanceId'],
            'machine': document['instanceType'],
            'private_ip': document['privateIp'],
            }

    return _INFO
