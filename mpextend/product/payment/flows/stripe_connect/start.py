#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Start Stripe transactions
"""
from django.urls import reverse
import stripe

from mpframework.common import log
from mpframework.common.utils import safe_int

from .common import SC
from .common import money_encode


def flow_start( request, apa, payto ):
    """
    Setup Stripe Connect checkout session based on APA.
    Creates or reuses customer on the payto account, and sets up a one-time
    or future payment depending on the APA.
    Group accounts can also add quantity on the Strip check screen.
    """
    from ...models import PayUsing

    user = request.user
    assert user and apa and payto

    stripe_id = payto.service_account
    payusing = PayUsing.objects.get_or_create( payto, apa )

    if not ( stripe_id and payusing ):
        log.info("PAY CONFIG - Bad Stripe flow: %s, %s -> %s, %s",
                    request.mpipname, payto, stripe_id, payusing)
        return None, reverse( 'payment_error', args=('stripe_connect',) )

    log.debug("Stripe process starting: %s, %s - %s", user, apa, request.POST)

    # Check if this user has already setup a payment
    apapay = payusing.get_apa_payment( apa )

    price = money_encode( apa.access_price )
    mode = 'setup' if apa.is_subscription and not price else 'payment'

    # Reuse or create new customer
    customer = None
    apacust = apapay.get( 'customer', {} )
    # Keep customer associated with APA if already defined
    if apacust:
        customer = stripe.Customer.retrieve( apacust['id'], **{
            'stripe_account': payto.service_account,
            })
    # Check for customer on this account by email
    # Use the most recent one that comes up - edge cases of
    # multiple customers can be resolve on Stripe dashboard
    if not customer:
        customers = stripe.Customer.list(**{
            'stripe_account': payto.service_account,
            'email': user.email,
            'limit': 1,
            })
        customer = customers.data and customers.data[0]
    # Otherwise create a new customer
    if not customer:
        customer = stripe.Customer.create(**{
            'stripe_account': payto.service_account,
            'name': user.name,
            'email': user.email,
            'metadata': {
                'user_id': user.id,
                'account_id': apa.account.id,
                },
            })

    session_options = {
        'stripe_account': payto.service_account,
        'customer': customer.id if customer else None,
        'mode': mode,
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': apa.pa.name,
                    'description': apa.description,
                    },
                'unit_amount': price,
                },
            'quantity': 1,
            }],
        'client_reference_id': apa.account.id,
        'metadata': {
            'apa': apa.pk,
            'payusing': payusing.pk,
            'payto': payto.pk,
            },
        'success_url': _add_session( request.build_absolute_uri(
                    reverse( 'payment_finish', args=('stripe_connect',) ) ) ),
        'cancel_url': _add_session( request.build_absolute_uri(
                    reverse( 'payment_cancel', args=('stripe_connect',) ) ) ),
        }

    # Setup support for future billing
    if apa.is_subscription:
        session_options.update({
            'payment_intent_data': {
                'on_behalf_of': payto.service_account,
                'setup_future_usage': 'off_session',
                },
            })

    # Allow group accounts to change units
    if apa.account.is_group:
        for line_item in session_options['line_items']:
            line_item['adjustable_quantity'] = {
                'enabled': True,
                }

    # Stripe requires tax objects, so store info for taxes in APA data
    tax = apa.account.get_tax()
    apatax = apapay.get( 'tax', {} )
    if tax:
        percent = safe_int( tax.get( 'percent', 0 ) * 100 )
        if percent and ( not apatax.get('id') or percent != apatax.get('percent') ):
            # Create new Stripe tax object if needed
            apatax = stripe.TaxRate.create( display_name=tax.get('name'),
                        percentage=percent, inclusive=False )
            if apatax:
                apapay.set( 'tax', apatax )
                for line_item in session_options['line_items']:
                    line_item['tax_rates'] = [ apatax.id ]
    # Clear an existing tax
    else:
        apapay.pop( 'tax', None )

    session = stripe.checkout.Session.create( **session_options )

    log.info("PAY STRIPE checkout: %s -> %s", request.mpipname, apa)
    log.debug("Stripe checkout: %s", session)

    payusing.set_apa_payment( apa, {
        'customer': {
            'id': customer.id,
            'email': customer.email,
            },
        'session': session.id,
        })
    payusing.save()

    return {
        'name': "Stripe",
        'public_key': SC['public_key'],
        'stripe_account': payto.service_account,
        'stripe_session': session,
        }, None


def _add_session( url ):
    return '{}?session_id={{CHECKOUT_SESSION_ID}}'.format( url )
