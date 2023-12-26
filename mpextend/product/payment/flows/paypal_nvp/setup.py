#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Paypal sub-view support for payment setup.

    ASSUMES DUCK-TYPING FROM setup.py code
"""
from django import forms

from mpframework.common.form import BaseForm
from mpframework.common.form import parsleyfy


ACCOUNT_NAME = 'paypal_account'


@parsleyfy
class SetupForm( BaseForm ):

    paypal_account = forms.CharField( required=False,
                widget=forms.TextInput(attrs={'size': '64'}) )


def handle_setup_form( request, form, payto ):
    """
    Handle saving of PayTo info
    """
    payto.service_account = form.cleaned_data.get('paypal_account')
    payto.save()
