#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User content usage API Views
"""

from mpframework.common import log
from mpframework.common.view import login_required
from mpframework.common.api import respond_api_call
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser

from ..models import ContentUser
from .bootstrap import user_tops
from .bootstrap import user_items


@login_required
def user_content( request ):
    """
    Provides the user's content usage
    """
    def handler( _get ):
        return {
            'collections': user_tops( request ),
            'items': user_items( request ),
            }
    return respond_api_call( request, handler, methods=['GET'] )

@login_required
def user_item( request ):
    """
    Create task to handle a user update request
    """
    def handler( values ):
        sandbox = request.sandbox
        if request.user.is_root:
            log.info2("Skipping root user_item: %s -> %s", request.mpipname, values)
            return
        log.debug("%s API user_item task: %s %s -> %s",
                    request.mptiming, request.method, request.mpipname, values)

        run_queue_function( _update_user_item, sandbox,
                    provider_id=sandbox.provider.pk,
                    sandbox_id=sandbox.pk,
                    user_id=request.user.pk,
                    values=values )

    return respond_api_call( request, handler, methods=['PUT', 'PATCH'] )

@mp_async
def _update_user_item( **kwargs ):
    """
    TAsk update status progress for individual content item
    """
    t = mpTiming()
    log.debug("%s Starting User item update: %s", t, kwargs)
    provider_id = kwargs.pop('provider_id')
    sandbox_id = kwargs.pop('sandbox_id')
    user_id = kwargs.pop('user_id')
    values = kwargs.pop('values')

    sandbox = Sandbox.objects.get_sandbox_from_id( sandbox_id, provider_id )
    user = mpUser.objects.get_from_id( sandbox, user_id )

    cu = ContentUser.objects.get_contentuser( user )
    if not cu:
        log.info("<- SUSPECT - Update without ContentUser: %s", user)
        return

    item_id = values.get('id')
    status = values.get('status')
    progress_data = values.get('progress_data')

    if 'S' == status:
        cu.start_item( item_id, progress_data )

    elif 'C' == status:
        cu.complete_item( item_id, progress_data )

    else:
        cu.update_item( item_id, progress_data )

    cui = cu.user_item( item_id )

    log.info("<- %s User item update: %s -> %s, %s", t, cui.item, status, cu)
