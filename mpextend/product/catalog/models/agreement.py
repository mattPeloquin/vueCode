#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Agreements / License Types

    Provide a flexible basis for how content licensing is managed, e.g.,
    user seats vs. metering, subscription, reuse, etc.
"""
from django.db import models
from django.db.models import Q

from mpframework.common import constants as mc
from mpframework.common.model.fields import YamlField
from mpframework.foundation.tenant.models.base import ProviderOptionalModel
from mpframework.foundation.tenant.models.base import TenantManager


class Agreement( ProviderOptionalModel ):
    """
    Agreements/"License types" provide a template for PAs that in
    turn are templates for APAs/Licenses.

    The Agreement template is completely defined by YAML rules that
    can be set in an Agreement, or modified by PAs, Coupons, and APAs.

    Implementation of Agreement rules is coordinated across MPF code.

    Default MPF behavior (i.e., no rules) for an APA/license:

      - All users tied to the APA have access
      - Content usage during the access period is not limited

    When pricing and/or metering is added to the rules:

      - APA.sku_units is 1-n
      - Base price is (unit_price * sku_units) for one access period
      - The base price covers (unit_points/users/minutes * sku_units) base usage
      - paygo increments are ( usage - base usage ) / paygo_points/users/minutes
      - (paygo_price * paygo increments) is charged for highest usage increments

    Agreement rules that define options for license creation/use:

      auto_renew            Make the license a subscription
      access_free           Force total price to always be free
      backoffice_payment    No automated payments; pricing only for reporting
      one_time_use          Only allow one use of the APA/license
      is_trial              Exclude 'no_trials' content from the license
      no_prompt             Do not prompt user if possible
      active_users_max      Hard cap on active users in access period
      initial_price         Added to first payment during license creation

    Unlike PAs, agreements are ProviderOptional, so a set of Agreements
    can be defined by the platform as well as customized per provider.
    """

    # Name used is the admin UI
    name = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT )

    # Licensing rules
    # Defines scope and fluid rule parameters for different agreement scenarios,
    # some of which can be overridden in PA and APA
    rules = YamlField( null=True, blank=True )

    # Toggle showing of Agreement as an option for PAs
    enabled = models.BooleanField( default=True )

    # Staff notes and information
    notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    # Display ordering for displaying in select boxes
    order = models.CharField( max_length=mc.CHAR_LEN_UI_CODE, blank=True )

    objects = TenantManager()

    class Meta:
        verbose_name = u"License type"

    def __str__(self):
        return self.name

    @staticmethod
    def is_active_Q():
        # May want to expand agreements with dates
        return(
            Q( enabled=True )
            )
