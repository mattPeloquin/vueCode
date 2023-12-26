#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared catalog form code
"""
from django import forms

from mpframework.common.form import BaseModelForm


class BaseCatalogFormMixin( BaseModelForm ):

    auto_renew = forms.BooleanField( required=False,
            label="Subscription",
            help_text="<span id='help_auto_renew'>"
                "Automatically renew license each <b>access period</b>.<br>"
                "The user must have a valid payment method enabled.<br>"
                "The license will be marked inactive if payment fails."
                "</span>" )
    max_renewals = forms.IntegerField( required=False,
            label="Maximum renewals",
            help_text="Set a limit to the number of access periods an ongoing "
                "subscription will renew.<br>"
                "Leave blank for a perpetual subscription." )
    is_trial = forms.BooleanField( required=False,
            label="Trial access",
            help_text="Prevent access to content that has 'No trials' set." )
    active_users_max = forms.IntegerField( required=False,
            label="Maximum active users per period",
            help_text="For group licenses, optionally limit the number of unique "
                "users that can access content each period." )
    initial_price = forms.DecimalField( required=False,
            max_digits=6, decimal_places=2,
            label="Initial price",
            help_text="Adds amount to first purchase (e.g., a setup fee)." )

    unit_points = forms.IntegerField( required=False,
            label="Base points",
            help_text="<span id='help_unit_points'>"
                "Optionally meter the content points available for use "
                "each <b>access period</b>.<br>"
                "</span>" )
    unit_users = forms.IntegerField( required=False,
            label="Base active users",
            help_text="<span id='help_unit_users'>"
                "Optionally meter the number of unique users "
                "that can use content each <b>access period</b>.<br>"
                "</span>" )
    unit_minutes = forms.IntegerField( required=False,
            label="Base usage minutes",
            help_text="<span id='help_unit_minutes'>"
                "Optionally limit the number of total minutes that can be "
                "use each <b>access period</b>.<br>"
                "</span>" )

    paygo_points = forms.IntegerField( required=False,
            label="PayGo points",
            help_text="<span id='help_paygo_points'>"
                "Set a number of content points that are "
                "added with each PayGo charge.<br>"
                "</span>" )
    paygo_users = forms.IntegerField( required=False,
            label="PayGo active users",
            help_text="<span id='help_paygo_users'>"
                "Set a number of additional active users added "
                "with each PayGo charge.<br>"
                "</span>" )
    paygo_minutes = forms.IntegerField( required=False,
            label="PayGo usage minutes",
            help_text="<span id='help_paygo_minutes'>"
                "Set a number of additional minutes added with "
                "each PayGo charge.<br>"
                "</span>" )

    yaml_form_fields = {
        '_rules': {
            'upstream_getter': 'rules',
            'form_fields': [
                '>>auto_renew', '>>max_renewals', '>>is_trial',
                'active_users_max', 'initial_price',
                'unit_points', 'unit_users', 'unit_minutes',
                'paygo_points', 'paygo_users', 'paygo_minutes',
            ] }
        }
