#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provide user information on history tracking
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.utils import tz
from mpframework.common.view import login_required
from mpextend.product.account.utils import get_account
from mpextend.user.usercontent.models import ContentUser


@login_required
def profile_history( request ):
    user = request.user

    # Content usage
    cu = ContentUser.objects.get_contentuser( user )
    usage = []
    if cu:
        for ui in cu.my_items_full.iterator():
            log.detail3("Adding user use row: %s", ui)
            try:
                usage.append({
                    'name': ui.item.name,
                    'tree': ui.top_tree.item.name if ui.top_tree else '',
                    'uses': ui.uses,
                    'license': ui.apa.name if ui.apa else '',
                    'minutes': ui.minutes_used,
                    'completed': tz( ui.completed ).date() if ui.completed else '',
                    'last_use': tz( ui.last_used ).date(),
                    'started': tz( ui.hist_created ).date(),
                    })
            except Exception as e:
                log.warning_quiet("Error creating use row: %s -> %s", ui, e)

    # License history
    apas = None
    account = get_account( user )
    if account:
        if account.is_group:
            apas = account.get_apas_dict( user=user )
        else:
            apas = account.get_apas_dict()

    return TemplateResponse( request, 'user/profile/history.html', {
                'usage': usage,
                'account': account,
                'apas': apas,
                })
