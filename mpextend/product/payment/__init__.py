#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    The payment app connects MPF sellers and buyers
    through external payment services.

    Payments work with APAs that have already been created, and simply
    try to charge the total value at a point in time for the APA.
    Price, subscriptions, units being purchases, etc. are are managed
    by the APA - the payment app only handles charging total amounts.
"""
