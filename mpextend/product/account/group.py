#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Decorators to support group admin functionality
"""
from functools import wraps
from django.conf import settings
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.utils import safe_int
from mpframework.common.utils import request_is_authenticated
from mpframework.common.utils.login import authenticate_error_response


class mpGroupAccountException( Exception ):
    """
    Handle cases where a group account screen cannot be displayed because
    no group account exists or permissions are insufficient.
    """
    pass


def group_admin_view( view_fn ):
    """
    Fixup and validate requests to group admin views

    Makes sure the user has privileges, converts group account id
    into account object, supports getting default account
    """
    from mpextend.product.account.models import GroupAccount

    @wraps( view_fn )
    def wrapper( request, *args, **kwargs ):
        user = request.user

        # Wrapper accepts GA id for account and converts it into an account object
        ga_id = kwargs.pop( 'ga_id', None )

        if request_is_authenticated( request ):
            try:
                log.debug("Getting GA admin view: %s -> %s", user, ga_id)

                # Set current account from GA id if provided
                account = None
                if safe_int( ga_id ):
                    ga = GroupAccount.objects.mpusing('read_replica')\
                            .get_quiet( request=request, id=ga_id )
                    if ga:
                        account = ga.base_account
                    else:
                        raise mpGroupAccountException(
                            "SUSPECT GA - bad group account: %s -> %s" %
                                (request.mpipname, ga_id))

                if user.access_staff:
                    log.info2("Allowing staff GA admin: %s -> %s, %s",
                                request.mpname, account, view_fn)
                    return view_fn( request, account, *args, **kwargs )

                if hasattr( user, 'account_user' ):
                    ua = user.account_user

                    # If no GA requested try user's primary account or
                    # the first account they are an admin of
                    if not account:
                        if ua.primary_account and ua.primary_account.is_group:
                            account = ua.primary_account
                        else:
                            admins = ua.active_admin_accounts
                            if admins:
                                account = admins[0]

                    # If user is a GA for the account, send them along
                    if ua.is_group_admin( account ):
                        log.info2("Allowing GA admin: %s -> %s, %s",
                                    request.mpname, account, view_fn)
                        return view_fn( request, account, *args, **kwargs )

                log.info("SUSPECT - Not allowing GA admin: %s -> %s",
                            request.mpipname, account)

            except mpGroupAccountException as e:
                log.warning( e )
                return HttpResponseRedirect( request.sandbox.portal_url() )

            except Exception:
                log.exception("Problem with account admin request")
                if settings.MP_TESTING:
                    raise

        return authenticate_error_response( request )
    return wrapper
