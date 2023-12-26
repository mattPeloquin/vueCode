#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Core onboard logic
"""
from django.conf import settings

from mpframework.common import log
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.foundation.tenant.models.provider import Provider
from mpframework.foundation.tenant.models.sandbox_host import SandboxHost
from mpframework.user.mpuser.models import mpUser
from mpframework.content.mpcontent.models import BaseItem
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon
from mpextend.product.account.models import GroupAccount


def onboard_clone_session( sandbox, session ):
    return onboard_clone( sandbox, session['sandbox_name'],
                         session['subdomain'], session['onboard_role'],
                         session['email'], session['password'] )

def onboard_clone( origin_sandbox, name, subdomain, onboard_role, email, password ):
    """
    Idempotent logic for new provider with starter sandbox from an existing sandbox.
    Usually this will be a fairly empty template sandbox, so tasks are not created
    to clone models (although models may use tasks for cloning internals).
    Returns the new Sandbox.
    The new owner user can be looked up via email.
    """
    onboard_data = settings.MP_ROOT_ONBOARD_SETUP
    if origin_sandbox.id not in onboard_data:
        log.warning("SUSPECT ATTACK - ONBOARD bad origin: %s -> %s",
                    origin_sandbox, onboard_data)
        return
    if any( c in name for c in settings.MP_INVALID_NAME['CHARS'] ):
        log.info2("SUSPECT - ONBOARD bad name: %s -> %s",
                    origin_sandbox, name)
        return
    if origin_sandbox.policy['disable_onboard']:
        log.info("ONBOARD aborted due to disable: %s -> %s",
                    origin_sandbox, name)
        return

    onboard = onboard_data[ origin_sandbox.id ]
    role = onboard[ onboard_role ]

    # Create provider
    policy = settings.MP_ROOT_ONBOARD_LEVELS[
                role['start_level'] ]['onboard_policy'].copy()
    policy.update({
        'site_limits': {
            'max_level': role['max_level'],
            }
        })
    log.info2("New Tenant: %s, %s -> %s", name, subdomain, policy)
    provider = Provider.objects.create_obj( name=name, system_name=subdomain,
                policy=policy )
    # Create sandbox
    source = Sandbox.objects.get( id=role['sandbox_to_clone'] )
    sandbox = Sandbox.objects.clone_sandbox( source, provider, name, subdomain,
                _email_staff=email, _policy={ 'level_key': role['start_level'] })
    if sandbox:
        # Default host URL name provided in onboarding
        host = settings.MP_ROOT.get('HOST_DB') or settings.MP_ROOT['HOST']

        SandboxHost.objects.create_obj( sandbox=sandbox,
                    _host_name='{}.{}'.format( subdomain, host ),
                    main=True, https=True )

        # Create the owner
        owner = mpUser.objects.create_obj( email, password, sandbox )
        owner._is_owner = True
        owner.is_superuser = True
        owner._staff_level = sandbox.policy.get( 'staff_level_max', 0 )
        owner.save()

        # Add content items, which will take care of copying any resources
        BaseItem.objects.clone_sandbox_objects( source, sandbox )

        # Add other items
        PA.objects.clone_sandbox_objects( source, sandbox )
        Coupon.objects.clone_sandbox_objects( source, sandbox )
        GroupAccount.objects.clone_sandbox_objects( source, sandbox )

    return sandbox
