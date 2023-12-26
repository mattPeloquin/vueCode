#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Stripe finish page sub-view
"""
import stripe
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from mpframework.common import log
from mpextend.product.account.models.apa import APA


def flow_end( request ):
    """
    Sub-view Stripe redirects to if payment successful.
    The payment will be in process, so if everything is in order,
    the APA is activated.
    """
    from ...models import PayTo
    from ...models import PayUsing
    user = request.user
    sandbox = request.sandbox

    payto = PayTo.objects.get_or_create( 'stripe_connect', sandbox=sandbox )
    session_id = request.GET.get('session_id')
    session = session_id and stripe.checkout.Session.retrieve( session_id, **{
            'stripe_account': payto.service_account,
            })
    if not session:
        return TemplateResponse( request, 'payment/failed.html', {} )

    # Get info sent with transaction; bail if not present
    customer, apa, payusing, apapay = None, None, None, None
    try:
        customer = stripe.Customer.retrieve( session.customer, **{
            'stripe_account': payto.service_account
            })
        apa = APA.objects.get( id=session.metadata['apa'], sandbox=sandbox )
        payusing = PayUsing.objects.get( id=session.metadata['payusing'],
                    sandbox=sandbox )
        apapay = payusing.get_apa_payment( apa )
    except Exception as e:
        log.debug("Stripe metatdata exception: %s", e)
    if not ( customer and apa and payusing and apapay ) or (
            apapay['session'] != session.id ):
        log.info("SUSPECT STRIPE bad data: %s | %s | %s | %s | %s | %s",
             apa, payto, payusing, apapay, session, customer )
        return TemplateResponse( request, 'payment/failed.html', {} )

    log.info2("PAY Stripe checkout success %s -> %s, %s", user, session_id, apa )
    log.debug("Stripe end: %s | %s | %s | %s | %s",
                payto, payusing, apapay, session, customer )

    # Activate the APA and store payment details
    apa.save( _user=user,
              _activate="Stripe payment: {}, {}".format(
                        session.amount_total / 100.0, session.id ) )

    # Update payment info
    apapay['success'] = True
    payusing.set_apa_payment( apa, apapay )
    payusing.save()

    # Show success screen or return to portal based on options
    if sandbox.options['payment.show_success']:
        return TemplateResponse( request, 'payment/success.html', {
                    'apa': apa,
                    'amount': session.amount_total,
                    'response': "Stripe Session ID {}".format( session.id ),
                    })
    else:
        return HttpResponseRedirect( sandbox.portal_url( 'sku', apa.pa.sku ) )
