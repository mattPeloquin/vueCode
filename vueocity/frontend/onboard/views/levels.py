#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Change provider level
"""
from time import sleep
from django.conf import settings
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.view import staff_required
from mpframework.common.cache.template import template_no_cache

from ...onboard import onboard_levels


@template_no_cache
@staff_required
def change_level( request ):
    """
    Redirection link that changes provider level and sends back to portal
    Only responds if onboarding is active.
    """
    log.info("ONBOARD change level: %s -> %s", request.mpipname, request.GET )
    try:
        user = request.user
        sandbox = request.sandbox
        if user.is_staff and user.is_owner and sandbox.policy.get('onboarding'):
            max_level = onboard_levels().get(
                    sandbox.policy.get('site_limits.max_level') )
            set_level = 0
            onboard_level = request.GET.get('onboard_level')
            onboard_info = onboard_levels().get( onboard_level )
            if onboard_info:
                if onboard_info['order'] > max_level['order']:
                    raise Exception("SUSPECT - provider level escalation")

                # Setup policy
                policy = onboard_info['onboard_policy']
                policy['level_key'] = onboard_level
                sandbox._policy.update( policy )
                sandbox.save()
                log.info("Sandbox provider level change: %s, %s -> %s",
                            user, sandbox, policy)

                set_level = policy['staff_level_max']

            # And then make sure owner can see
            user.set_max_level( set_level, save=True )

            # HACK - buffering can mess up reload after change level, so wait it out
            # This view runs on FT servers so blocking isn't a major concern
            sleep( settings.MP_CACHE_AGE['BUFFER_VERSION'] )

            # Send back to portal for complete reload
            referer = request.referrer or request.sandbox.portal_url()
            log.info2("Level redirect: %s -> %s", onboard_level, referer)
            return HttpResponseRedirect( referer )

    except Exception as e:
        if settings.MP_DEV_EXCEPTION:
            raise
        log.warning("Change level error: %s -> %s", request.mpipname, e)

    log.info("Did not complete change_level: %s", request.mpipname)
    return HttpResponseRedirect( request.sandbox.portal_url() )
