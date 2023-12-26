#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test and debug Views
"""
from django import forms
from django.template.response import TemplateResponse

from mpframework.common.view import root_only
from mpframework.common.logging.utils import pretty_print

from ..payment_types import PAYMENT_TYPES


@root_only
def mptest_paypal( request ):

    call_paypal = PAYMENT_TYPES['paypal_nvp']['flow'].common.call_paypal_nvp

    trans_details = ""

    class PaypalTransForm( forms.Form ):
        transaction_id = forms.CharField(required=False, label="Transaction ID to lookup")

    if 'POST' == request.method:
        form = PaypalTransForm( request.POST )
        if form.is_valid():

            trans_details = call_paypal({
                    'METHOD': 'GetTransactionDetails',
                    'TRANSACTIONID': form.cleaned_data.get('transaction_id'),
                    })

    else:
        form = PaypalTransForm()

    return TemplateResponse( request, 'root/test/paypal.html', {
                'form': form,
                'trans_details': pretty_print(trans_details),
                })


@root_only
def mptest_stripe( request ):

    return TemplateResponse( request, 'root/test/stripe.html', {
                })
