#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Information related to address and other non-email contact information
"""

from django.db import models

from .. import constants as mc
from .fields import CountryField


class ContactMixin( models.Model ):
    """
    Contractual and contact information related to a real-world person
    or company. This may be used both for storing information necessary to
    process billing payments, as well as information required for
    customer support.

    All systems users do NOT need a contact record, so this information
    is intentionally decoupled from the user information.
    """

    # Physical Address
    street = models.CharField( max_length=mc.CHAR_LEN_UI_LINE, blank=True )
    city = models.CharField( max_length=mc.CHAR_LEN_UI_LINE, blank=True )
    state = models.CharField( max_length=mc.CHAR_LEN_UI_LINE, blank=True )
    postal_code = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, blank=True )
    country = CountryField()

    # Phone
    phone = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, blank=True )
    phone2 = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT, blank=True )

    class Meta:
        abstract = True
