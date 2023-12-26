#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric tasks that execute Django management commands
    on the target server
"""

from mpframework.deploy.fab.decorators import mptask
from mpframework.deploy.fab.decorators import prod_warn
from mpframework.deploy.fab.shell import show_mem
from mpframework.deploy.fab.shell import show_disk
from mpframework.deploy.fab.utils import *


@mptask
def show_code( c ):
    """Show code revision"""
    runcmd( c, ['hg summary'] )

@mptask
def show_full( c ):
    """Show code revision"""
    show_code( c )
    show_mem( c )
    show_disk( c )

@mptask
@prod_warn
def db_dumpscript( c, pid ):
    """
    Put DB dump into db_data.py
    HACK -- dump knows about mpextend
    FUTURE - dumpscript is out of date
    """
    models = (
        'tenant.provider tenant.sandbox ' +
        'user.mpuser user.usertracking ' +
        'mpcontent.portaltype mpcontent.portalcategory mpcontent.portalgroup' +
        'mpcontent.tree mpcontent.tree_categories mpcontent.treebaseitem ' +
        'mpcontent.protectedfile mpcontent_extend.video mpcontent_extend.lmsitem ' +
        'mpcontent_extend.protalitem mpcontent_extend.pdf' +
        'mpcontent_extend.page mpcontent_extend.embed mpcontent_extend.quiz mpcontent_extend.proxylink mpcontent.proxyapp ' +
        'catalog.agreement catalog.pa catalog.coupon ' +
        'account.account account.accountuser account.groupaccount account.apa ' +
        'payment.pay_event payment.pay_to payment.pay_using ' +
        'usercontent.contentuser usercontent.useritem usercontent.badge' +
        'plan.baseplan plan.userplan plan.groupplan '
        )
    excludes = ['baseitem_ptr']
    fixups = ['mpuser.mpuser']
    rundj( c, 'db_dumpscript -v3 --pid %s --exclude_field_list "%s" --fixup_list "%s" %s > db_data.py' %
                (pid, excludes, fixups, models) )

@mptask( optional=['arg_string'] )
@prod_warn
def manage( c, command_str, arg_string=":" ):
    """
    DJ manage: fab manage xyz arg1,arg2:kwarg1=val,kwarg2=val
    Fab2 doesn't have arg or kwarg support, so add crude version here
    """
    args, kwstrs = arg_string.split(':')

    args = args.split(',')
    kwstrs = kwstrs.split(',')
    kwargs = {}
    for kwstr in kwstrs:
        if kwstr:
            key, value = kwstr.split('=')
            kwargs[ key ] = value
    rundj( c, command_str, *args, **kwargs )
