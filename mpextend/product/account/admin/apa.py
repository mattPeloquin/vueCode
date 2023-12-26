#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account Product Agreement admin
"""
from django import forms

from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.utils import safe_int
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.common.admin.large import AdminLargeMixin
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.content.mpcontent.tags import tag_code_help
from mpextend.product.catalog.models import Agreement
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.admin.base_form import BaseCatalogFormMixin

from ..models import APA
from ..models import GroupAccount
from .au_mixin import AccountUsersFields


class ApaForm( BaseCatalogFormMixin, BaseModelForm ):
    autolookup_fields = ('account', 'pa')
    class Meta:
        model = APA
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'account': "Account",
            'pa': "Pricing option",
            '_is_active': "License available for use",
            '_unit_price': "Override base price",
            '_access_period': "Override access period",
            '_tag_matches': "Override license tags",
            '_paygo_price': "PayGo price",
            'sku_units': "SKU units",
            'period_end': "Access period end",
            'access_end': "Fixed expiration date",
            'ga_license': "Include all users in group account",
            'ga_users': "Limit to specific users",
            'ga_users_max': "Maximum users",
            'custom_name': "Custom description",
            'purchase_type': "Creation type",
            'period_start': "Access period start",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'account': "Account or user using this license",
            'pa': "<span id='help_pa_notes'>"
                    "Select the pricing option for user access.<br>"
                    "Pricing, timing, and options may be customized "
                    "after creation."
                    "</span>",
            '_is_active': "Disabling this license will immediately suspend "
                    "content access. Disabled licenses will not renew and "
                    "will not attempt future subscription payments.",
            'period_end': "Date when the current <b>access period</b> ends.<br>"
                    "Leave blank for a perpetual license.<br>"
                    "Licenses may be renewed manually or with <b>subscriptions</b>.<br>"
                    "Pricing is recalculated when the next period starts.<br>"
                    "{help_license_pricing}",
            '_tag_matches': tag_code_help(
                    "Optionally override pricing option content.<br>"),
            '_access_period': "Leave blank to use <b>pricing option</b> access period"
                    "<span id='help_access_period'></span>.<br>"
                    "You can set a specific access period (e.g., '2 weeks') or <br>"
                    "enter <b>perpetual</b> (or just 'p') to force a perpetual license.<br>"
                    "{help_license_pricing}",
            '_unit_price': "Leave blank to use <b>pricing option</b> base price"
                    "<span id='help_unit_price'></span>.<br>"
                    "Optionally override for future renewals of this license.<br>"
                    "<b>Subscriptions</b> automatically charge this price,<br>"
                    "<b>backoffice payments</b> use it for reporting.<br>"
                    "{help_license_pricing}",
            '_paygo_price': "<span id='help_paygo_price'>"
                    "Leave blank to use <b>pricing option</b> PayGo usage metering.<br>"
                    "Optionally override to set a PayGo price for each PayGo "
                    "increment after <b>base price</b> usage is consumed.<br>"
                    "{help_license_metering}"
                    "</span>",
            'sku_units': "Number of SKU/<b>pricing option</b> units in this license.<br>"
                    "Used for automated charging, multiplying base price by units.<br>"
                    "Changes to units take effect the NEXT <b>access period</b>.",
            '_rules': "Add or overwrite pricing option or license rules",
            'ga_users_max': "Limit the number of users that can be invited to "
                    "this license.",
            'ga_users': "Add account users to this license",
            'access_end': "Optionally set a fixed date for this license to end.<br>"
                    "This overrides <b>access period</b> and subscriptions "
                    "will not be renewed after this date.<br>",
            'ga_license': "Give all <b>group account</b> users access.<br>"
                    "Uncheck to select specific group account users for the license.",
            'period_start': "Date when current access period started or will start<br>"
                    "Leave blank for new license to start immediately.",
            'custom_name': "Optional custom description for this license.",
            'purchase_type': "How was this license created?",
            'coupon': "Coupon code used for trial or purchase",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            '_tag_matches': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            '_rules': CodeEditor( mode='yaml', theme='default', rows=12 ),
            'data': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })

    usage_points = forms.IntegerField( required=False,
            label="Points used",
            help_text="The total content points used in this access period." )
    usage_users = forms.IntegerField( required=False,
            label="Active users",
            help_text="The number of active users in this access period." )
    usage_seconds = forms.IntegerField( required=False,
            label="Total seconds",
            help_text="The total content seconds used this access period." )
    history = forms.CharField( required=False,
            widget=forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            label="History and staff notes",
            help_text="Historical events related to the license.<br>"
                    "Staff can modify and add to this history." )
    renewals = forms.IntegerField( required=False,
            label="Previous renewals",
            help_text="Number of times this license has been renewed." )
    total_paid = forms.DecimalField( required=False,
            max_digits=8, decimal_places=2,
            label="Total paid",
            help_text="The amount paid toward this license since creation." )

    yaml_form_fields = BaseCatalogFormMixin.yaml_form_fields.copy()
    yaml_form_fields.update({
        'data': {
            'form_fields': [
                'usage_points', 'usage_users', 'usage_seconds',
                'history', 'total_paid', 'renewals',
                ]
            }
        })

#--------------------------------------------------------------------

class ActiveFilter( mpListFilter ):
    """
    The admin view of active combines the active and activated flags to
    allow simple user override of off/on.
    """
    title = "License state"
    parameter_name = 'state'
    def lookups( self, request, model_admin ):
        return [ ( 'active', "Active" ),
                 ( 'inactive', "Inactive" ),
                 ]
    def queryset( self, request, qs ):
        if self.value() == 'active':
            return qs.filter( _is_active=True, is_activated=True )
        if self.value() == 'inactive':
            return qs.exclude( _is_active=True, is_activated=True )

class FreeFilter( mpListFilter ):
    """
    Separate different free and purchase types
    """
    title = "Free vs. Paid"
    parameter_name = 'free'
    def lookups( self, request, model_admin ):
        return (
            ('paid', 'All paid access'),
            ('free', 'All free access'),
            ('paidonline', 'Online purchases'),
            ('paidbackoffice', 'Backoffice purchases'),
            ('freeonline', 'Free (excluding backoffice)'),
            )
    def queryset( self, request, qs ):
        if self.value() == 'paid':
            return qs.exclude( APA.is_free_Q()  )
        if self.value() == 'free':
            return qs.filter( APA.is_free_Q() )
        if self.value() == 'paidonline':
            return qs.exclude( APA.is_free_Q() ).exclude( purchase_type='B' )
        if self.value() == 'paidbackoffice':
            return qs.exclude( APA.is_free_Q() ).filter( purchase_type='B' )
        if self.value() == 'freeonline':
            return qs.filter( APA.is_free_Q() ).exclude( purchase_type='B' )

class GroupAccountFilter( mpListFilter ):
    """
    Allow seperation of both group accounts, and individual from groups
    """
    title = "Group Accounts"
    parameter_name = 'ga'

    def lookups( self, request, model_admin ):
        # Get list of group accounts in this sandbox
        group_accounts = GroupAccount.objects.filter( request=request )
        # Create lookup list
        return [
                ( '-1', "Only individual purchases" ),
                ( '0', "Hide individual purchases" ),
                ] + [ (ga.pk, str(ga)) for ga in group_accounts ]
    def queryset( self, request, qs ):
        if self.value() is None or self.value() == 'all':
            return
        selection = safe_int( self.value() )
        if selection > 0:
            return qs.filter( account_id=selection )
        else:
            hide_groups = bool( selection < 0 )
            return qs.filter( account__group_account__isnull=hide_groups )

class SubscriptionFilter( mpListFilter ):
    title = "Subscription"
    parameter_name = 'subscription'
    def lookups( self, request, model_admin ):
        return [ ( 'auto', "Subscription" ),
                 ( 'manual', "Manual renewal" ),
                 ( 'single', "Single use" ),
                 ]
    def queryset( self, request, qs ):
        auto = APA.is_subscription_Q() & APA.is_reusable_Q()
        if self.value() == 'auto':
            return qs.filter( auto ).distinct()
        if self.value() == 'manual':
            return qs.exclude( auto ).distinct()
        if self.value() == 'single':
            return qs.exclude( APA.is_reusable_Q() ).distinct()

# Make filter drop-downs tenant aware
PAsFilter = mpListFilter.new( PA, u"Pricing option", 'pa_id' )
AgreementFilter = mpListFilter.new( Agreement, u"License type",
            'pa__agreement_id' )

#--------------------------------------------------------------------

class ApaBaseAdmin( AccountUsersFields, BaseTenantAdmin ):
    form = ApaForm

    list_display = ( 'account', 'user_info', 'name',
            'period_end', 'subscription', 'price', 'units',
            'purchase_type', 'license_type', 'metering',
            'tags', 'coupon', 'hist_modified', 'hist_created' )
    list_text_small = BaseTenantAdmin.list_text_small + (
            'active', 'user_info', 'period_end', 'price',
            'units', 'purchase_type', 'subscription',
            'name', 'license_type', 'metering', 'tags', 'coupon' )
    list_col_small = BaseTenantAdmin.list_col_small + (
            'active', 'enabled', 'units',
            'uses_current', 'uses_max' )
    list_col_med = BaseTenantAdmin.list_col_med + (
            'user_info', 'name', 'period_end', 'subscription', 'tags',
            'license_type', 'metering', 'purchase_type', 'coupon' )
    list_hide_med = BaseTenantAdmin.list_hide_med + (
            'license_type', 'metering', 'tags' )
    list_hide_small = BaseTenantAdmin.list_hide_small + (
            'units', 'purchase_type', 'coupon' )

    list_filter = ( ActiveFilter, FreeFilter, SubscriptionFilter,
            GroupAccountFilter, 'purchase_type', AgreementFilter, PAsFilter,
            'period_end', 'hist_modified', 'hist_created' )
    list_filter_options = {
        'ActiveFilter': { 'default': 'active' },
        'FreeFilter': { 'default': 'all' },
        }

    search_fields = ( 'pa__sku', 'account__name', 'coupon', 'custom_name', 'data',
                      # FUTURE - can cause 30+ second queries
                      #'=account__primary_aus__user__email',
                      #'=ga_users__user__email',   # GA users
                      )

    # License relationships cannot be modified once created
    readonly_fields = BaseTenantAdmin.readonly_fields + (
                'purchase_type', )

    filter_horizontal = ( 'ga_users' ,)

    # For initial admin create, only a subset is available until PA is set
    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': [
                ('account', 'pa'),
                ('period_end', 'auto_renew'),
                ('_unit_price', '_access_period'),
                '_is_active',
                ]
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse',),
            'fields': (
                'is_activated',
                '_rules',
                'data',
                )
            }),
        ]
    after_create_fieldsets = [
        (_("Usage metering"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('_paygo_price',),
                ('unit_points', 'paygo_points', 'usage_points'),
                ('unit_minutes', 'paygo_minutes', 'usage_seconds'),
                ]
            }),
        (_("Options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('sku_units', '_tag_matches'),
                ('max_renewals', 'renewals'),
                ('period_start', 'access_end'),
                'custom_name',
                ]
            }),
        (_("History"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('purchase_type', 'coupon'),
                'total_paid',
                ('hist_modified', 'hist_created'),
                'history',
                ]
            }),
        ]

    @property
    def can_ajax_save( self ):
        return False

    def save_model( self, request, obj, _form, _change ):
        obj.save( _user=request.user, _admin=True )

    def get_object( self, request, *args ):
        """
        Apply overrides from control_apas, make active track activate
        """
        obj = super().get_object( request, *args )
        if obj:
            obj.apply_pa_override()
            if not obj.is_activated:
                obj._is_active = False
        return obj

    def get_list_display( self, request ):
        rv = list( super().get_list_display( request ) )
        if ActiveFilter.parameter_name in request.GET:
            rv.insert( 2, 'active' )
        return rv

    def get_readonly_fields( self, request, obj=None ):
        """
        Allow for backoffice creation of APAs, but after any type
        of creation limit what can be modified.
        """
        user = request.user
        rv = self.readonly_fields
        if obj and not user.logged_into_root:
            rv += ( 'account', 'pa' )
            if obj.pa.control_apas:
                rv += obj.pa_control_fields
        return rv

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust screen controls based on the type of APA.
        Assumes APA type is defined before screen is created, such that the screen
        will not morph to reflect user settings when creating new APA.
        """
        rv = super().get_fieldsets( request, obj )

        # Add group account support
        if obj and obj.account.is_group:
            rv[0][1]['fields'].append( ('ga_license', 'ga_users_max') )
            rv[0][1]['fields'].append( ('ga_users',) )
            rv[1][1]['fields'].append( ('unit_users', 'paygo_users', 'usage_users') )

        return rv

    def get_queryset( self, request ):
        qs = super().get_queryset( request )

        # Explicitly set sandbox to avoid provider users from seeing
        # users' apas from other sandboxes
        qs = qs.filter( sandbox=request.user.sandbox )

        return qs

    # Active element is needed to call model property, as the _is_active field
    # doesn't get updated if has expired until it is touched
    def active( self, obj ):
        return obj.is_active( save=True, deep=True )
    active.short_description = "Active"
    active.admin_order_field = '_is_active'
    active.boolean = True

    def user_info( self, obj ):
        return obj.user_info
    user_info.short_description = ""

    def price( self, obj ):
        return obj.access_price
    price.short_description = "Price"

    def units( self, obj ):
        return obj.sku_units
    units.short_description = "Units"

    def tags( self, obj ):
        return obj.tag_matches
    tags.short_description = "License tags"

    def subscription( self, obj ):
        return obj.is_subscription
    subscription.short_description = "Subscription"
    subscription.boolean = True

    def name( self, obj ):
        return obj.custom_name or obj.pa.name
    name.short_description = "Pricing option"
    name.admin_order_field = 'pa___name'

    def license_type( self, obj ):
        return obj.pa.agreement.name
    license_type.short_description = "License type"
    license_type.admin_order_field = 'pa__agreement__name'

    def metering( self, obj ):
        return obj.metering_desc
    metering.short_description = "Metering"

#--------------------------------------------------------------------

class ApaStaffAdmin( StaffAdminMixin, AdminLargeMixin, ApaBaseAdmin ):
    helptext_changeform_add = _("Create a new account license based on a "
            "pricing option.<br>"
            "Additional options can be modified after creation.")

staff_admin.register( APA, ApaStaffAdmin )


class ApaRootAdmin( AdminLargeMixin, ApaBaseAdmin ):

    list_display = ApaBaseAdmin.list_display + ( 'activated', )

    def activated( self, obj ):
        return obj.is_activated
    activated.short_description = "Activated"
    activated.admin_order_field = 'is_activated'
    activated.boolean = True

root_admin.register( APA, ApaRootAdmin )
