#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared AWS-specific code

    Boto is used for interacting with existing, properly configured AWS
    services - AWS resources are provisioned/configured with TerraForm.
"""

from .session import get_client
from .session import get_resource
