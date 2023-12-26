#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account admin modifiable settings
"""
from django import forms
from django.template.response import TemplateResponse

from mpframework.common.form import BaseModelForm
from mpframework.common.cache.template import full_path_cache
from mpextend.product.account.models import Account
from mpextend.product.account.models import GroupAccount

from ...group import group_admin_view
from ._common import ga_admin_common


@full_path_cache
@group_admin_view
def ga_settings( request, account ):
    """
    Sceen fo editing details and options modifiable by admin
    """
    account, context = ga_admin_common( request, account )

    # Manage updates in the form
    if request.method == "POST":
        account_form = AccountForm( request.POST, instance=account )
        if account_form.is_valid():
            account_form.save()
        ga_form = GroupAccountForm( request.POST, instance=account.group_account )
        if ga_form.is_valid():
            ga_form.save()
    else:
        account_form = AccountForm( instance=account )
        ga_form = GroupAccountForm( instance=account.group_account )

    context.update({
            'form': account_form,
            'ga_form': ga_form,
             })

    return TemplateResponse( request, 'group/settings.html', context )


class AccountForm( BaseModelForm ):
    class Meta:
        model = Account
        exclude = ()

        fields = ( 'name', 'city', 'state', 'postal_code', 'country',
                   'phone', 'phone2' )

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'name': forms.TextInput( attrs={'size': 50 } ),
            'city': forms.TextInput( attrs={'size': 50 } ),
            })

class GroupAccountForm( BaseModelForm ):
    class Meta:
        model = GroupAccount
        exclude = ()

        fields = ( 'invite_code', 'image', 'external_key', 'external_group',  )

        widgets = dict( BaseModelForm.Meta.widgets, **{
            })
