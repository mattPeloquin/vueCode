#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Onboard context to add to templates
"""
from django.urls import reverse

from mpframework.common.cache.template import QUERYSTRING_PREFIX_CACHE

from . import onboard_levels


def onboard( request ):
    user = request.user
    rv = {
        # HACK - store URLs for tutorial screens
        'onboard_tutorial_sandbox': reverse('easy_sandbox'),
        'onboard_tutorial_product': reverse('easy_add_product'),
        }
    if user and user.access_staff_view:

        # Show provider onboard tool if appropriate
        if user.is_owner:
            policy = user.provider.policy
            if policy.get('onboarding') and not request.is_popup:
                # Update context with list of options available for this provider
                max_level = onboard_levels().get( policy.get('site_limits.max_level') )
                if max_level:
                    available_levels = []
                    for key, level in onboard_levels().items():
                        if level['show'] and level['order'] <= max_level['order']:
                            level['key'] = key
                            available_levels.append( level )
                    rv.update({
                        'onboard_help': {
                            'levels': available_levels,
                            },
                        })

        # Inject context variable with path to tutorial if selected
        tutorial = request.GET.get( QUERYSTRING_PREFIX_CACHE + 'tutorial' )
        if tutorial:
            rv.update({
                'onboard_tutorial': '{}/tutorials/'.format( tutorial ),
                })

    return rv
