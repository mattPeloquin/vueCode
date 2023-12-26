#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    AWS code for accessing AWS credentials and information.
"""
import json
import yaml
import boto3

from ..deploy.paths import home_path
from .ec2 import aws_instance_info


# FUTURE SECURE - don't cache or encrypt cached copy in case of compromised machine memory
_SECRETS = {}

def _get_secrets():
    """
    Get _SECRETS from the AWS Secrets store or local file if non-EC2 instance
    that needs to make calls to AWS.
    """
    global _SECRETS
    if _SECRETS:
        return _SECRETS
    info = aws_instance_info()
    try:

        # Try reading from local file
        # Can be used for dev cases, should not be used for production
        with open( home_path('.secrets', 'aws.yaml') ) as aws_file:
            aws = yaml.safe_load( aws_file )
            _SECRETS = aws['SECRETS']

    except IOError:
        # Get secrets from AWS manager
        region = info['region']
        secrets_id = 'prod/server'
        session = boto3.session.Session()
        client = session.client(
            service_name = 'secretsmanager',
            region_name = region,
            endpoint_url = 'https://secretsmanager.{}.amazonaws.com'.format( region )
            )
        secrets = client.get_secret_value(
            SecretId = secrets_id
            )
        _SECRETS = json.loads( secrets['SecretString'] )

    # Fixup secrets
    if not info['outside_aws']:
        # AWS secrets wouldn't store newlines and CF needs it to recognize pem
        key = str( _SECRETS['cf-key'] )
        key = ( '-----BEGIN RSA PRIVATE KEY-----\n' + key +
                    '\n-----END RSA PRIVATE KEY-----' )
        _SECRETS['cf-key'] = key

    return _SECRETS


def aws_s3_credentials():
    secrets = _get_secrets()
    return secrets.get( 's3_access_key', '' ), secrets.get( 's3_access_secret', '' )

def aws_s3_upload_credentials():
    secrets = _get_secrets()
    return secrets.get( 's3_upload_key', '' ), secrets.get( 's3_upload_secret', '' )

def aws_cf_credentials():
    secrets = _get_secrets()
    return secrets.get( 'cf-keyid', '' ), secrets.get( 'cf-key', '' )

def aws_email_credentials():
    secrets = _get_secrets()
    return secrets.get( 'email-user', '' ), secrets.get( 'email-pwd', '' )

def aws_db_credentials():
    secrets = _get_secrets()
    return secrets.get( 'db-user', '' ), secrets.get( 'db-pwd', '' )
