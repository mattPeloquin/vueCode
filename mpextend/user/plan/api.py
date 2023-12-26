#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plan web service API
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.api import respond_api_call
from mpframework.common.view import login_required
from mpframework.common.api import api_get_id

from .models import BasePlan
from .models import UserPlan


def get_user_plans( request ):
    """
    Send this user's plan, and any visible plans the user can see
    for use in viewmodels
    """
    log.debug2("Adding plan items: %s", request.user)
    rv = []
    try:
        for plan in UserPlan.objects.get_plans( request.user ):
            values = {}
            values['id'] = plan.pk
            values['name'] = plan.name
            values['nodes'] = plan.top_ids
            rv.append( values )

    except Exception as e:
        log.info("Problem getting user plan: %s -> %s", request.mpipname, e)
        if settings.MP_TESTING:
            raise
    return rv

@login_required
def plans( request ):
    """
    Get plan model data
    """
    user = request.user
    def handler( _get ):
        if user:
            log.debug2("API plans: %s", user)
            return {
                'plans': get_user_plans( request ),
                }
        log.debug("API plans called for inactive user: %s", user)
    return respond_api_call( request, handler, methods=['GET'] )

@login_required
def tree_plan( request ):
    """
    Modify tree nodes in a plan

    Will create a default user plan if no plan is specified, otherwise the
    requested plan ID must exists as a User or Group plan.
    All updates are in in the concrete BasePlan values.
    """
    def handler( payload ):
        user = request.user
        action = payload.get('action')
        tree_id = api_get_id( payload.get('tree_id') )
        plan_id = api_get_id( payload.get('plan_id') )
        log.debug("API tree_plan: %s, %s -> %s, %s", action, user, tree_id, plan_id)

        if plan_id:
            plan = BasePlan.objects.get_quiet( request=request, id=plan_id )
        else:
            log.debug("No plan, using default: %s -> %s", user, tree_id)
            plan = UserPlan.objects.get_or_create( user )

        if plan:
            if 'ADD' == action:
                plan.add_tree( user, tree_id )
            elif 'REMOVE' == action:
                plan.remove_tree( user, tree_id )
            return plan.hist_modified

        log.warning("SUSPECT - No plan available in tree_plan: %s, %s -> %s, %s",
                        request.mpipname, action, tree_id, plan_id)

    return respond_api_call( request, handler, methods=['POST'] )
