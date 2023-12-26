#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for specialized Admin calls
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import root_only
from mpframework.user.mpuser.models import mpUser
from mpframework.content.mpcontent.models import BaseItem
from mpextend.product.account.models import APA
from mpextend.product.account.models import Account
from mpextend.product.account.models import AccountUser
from mpextend.product.account.models import GroupAccount


@root_only
def fixups( request ):
    if 'POST' == request.method:
        try:
            # Shared items - not all are used for each type of action
            commit = bool( request.POST.get('validate') == 'HELL YA' )

            # Is this request targeted at specific sandboxes?
            sandbox_ids = None
            if 'sandbox_ids' in request.POST:
                sandbox_ids = request.POST.get('sandbox_ids', request.user.sandbox.pk).split()
                log.info("%s -- Performing sandbox updates: %s", request.user, sandbox_ids)

            # Account fixup

            if 'account_migrate' in request.POST:
                ga = request.POST.get('migrate_ga')
                if ga:
                    GroupAccount.objects.hard_migrate_all_users( ga )

            if 'account_merge' in request.POST:
                user = request.POST.get('user')
                account = request.POST.get('account')
                if user and account:
                    AccountUser.objects.merge_accounts( user, account )

            # Health checks
            manager = None

            if 'health_users' in request.POST:
                log.info("%s -- UPDATING USER HEALTH!", user)
                manager = mpUser.objects

            if 'health_content' in request.POST:
                log.info("%s -- UPDATING CONTENT ITEMS HEALTH!", user)
                manager = BaseItem.objects

            if manager:
                items = []
                if sandbox_ids:
                    items = manager.filter( sandboxes__in=sandbox_ids )
                else:
                    items = manager.all()

                if commit:
                    for item in items:
                        item.health_check()

        except Exception:
            log.exception("Problem with admin call in ops view")

    return TemplateResponse( request, 'root/ops/fixups.html', {
                 })
