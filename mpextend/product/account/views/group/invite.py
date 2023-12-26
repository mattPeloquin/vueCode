#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Add users to Group account via signup and invite
"""
from django.core.cache import caches
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.utils import get_random_key
from mpframework.common.form import BaseModelForm
from mpframework.common.cache.template import full_path_cache
from mpframework.user.mpuser.views.login  import login_create
from mpframework.user.mpuser.utils.login import logout_user
from mpextend.product.account.models import APA
from mpextend.product.account.models import GroupAccount
from mpextend.product.catalog.models import Coupon

from ...group import group_admin_view
from ._common import ga_admin_common


_cache = caches['session']


def ga_login_apa( request, ga_id, apa_id ):
    return _ga_login( request, ga_id, apa=apa_id )

def ga_login_coupon( request, ga_id, coupon_slug=None ):
    return _ga_login( request, ga_id, coupon=coupon_slug )

def ga_login( request, ga_id ):
    return _ga_login( request, ga_id )

def _ga_login( request, ga_id, apa=None, coupon=None ):
    """
    Account invite EasyLinks
    Sets up extra information for group account login before
    handling off to shared login code.
    """
    user = request.user
    sandbox = request.sandbox
    log.debug2("ga_login: %s -> %s, a/c %s/%s ", sandbox, ga_id, apa, coupon)
    account_info = {}
    try:
        ga = GroupAccount.objects.get_from_id( sandbox, ga_id )
        if ga:
            account_info.update({
                'name': ga.base_account.name,
                'group_account': ga,
                'create_code': ga.invite_code,
                'login_code': ga.invite_code,

                # FUTURE - make login templates custom
                'template': 'group/login_message.html',
                })

            # Add info for adding GA and APA into temp session
            session = {
                'sandbox': sandbox.pk,
                'ga_id': ga.pk,
                'apa_id': apa,
                'coupon_slug': coupon,
                }
            token = get_random_key( prefix='ga' )
            _cache.set( token, session )

            # Add extra login info that will redirect to extra portal, which
            # will process the session after login
            account_info.update({
                'portal_extra': { 'ename': 'account', 'evalue': token }
                })

            # If user is not already group account member, log them out so they
            # will be forced to signup at the login screen
            if user and user.is_authenticated:
                if not ga.has_user( user ):
                    logout_user( request )

            log.info("GA invite: %s, %s -> %s, a/c %s/%s", sandbox, user, ga, apa, coupon)
    except Exception as e:
        log.info2("SUSPECT - GA invite failed %s: %s, %s, %s -> %s",
                    request.mpipname, ga_id, apa, coupon, e)

    return login_create( request, login_extra=account_info )

#------------------------------------------------------------------------

@full_path_cache
@group_admin_view
def ga_invite( request, account ):
    """
    GA screen for invites
    """
    account, context = ga_admin_common( request, account )

    # Handle the form elements
    if request.method == "POST":
        form = GroupAccountInviteForm( request.POST, instance=account.group_account )
        if 'update_code' in request.POST:
            form.save()
    else:
        form = GroupAccountInviteForm( instance=account.group_account )

    # Are there eligible APAs to add to links?
    available_apas = APA.objects.get_apas( account, backoffice=True,
                                            available=True )
    unavailable_apas = APA.objects.get_apas( account, backoffice=True,
                                            not_available=True )

    # Are there eligible coupons to add to links?
    # They must have a PA, match account codes, and be free
    if account.codes:
        active_coupons = Coupon.objects.get_active_coupons( sandbox=request.sandbox,
                                ga_codes=account.codes, pa=True, free=True )
    else:
        active_coupons = []

    context.update({
            'form': form,
            'available_apas': available_apas,
            'unavailable_apas': unavailable_apas,
            'active_coupons': active_coupons,
            })
    return TemplateResponse( request, 'group/invite.html', context )

class GroupAccountInviteForm( BaseModelForm ):
    """
    Combined form to handle user input for different invite scenarios
    """
    class Meta:
        model = GroupAccount
        exclude = ()
        fields = ( 'invite_code' ,)
