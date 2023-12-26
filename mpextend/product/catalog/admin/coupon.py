#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for coupon models
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.content.mpcontent.tags import tag_code_help

from ..models import Coupon
from ..models import PA
from .base_form import BaseCatalogFormMixin


class CouponForm( BaseCatalogFormMixin, BaseModelForm ):
    autolookup_fields = ('pa',)
    class Meta:
        model = Coupon
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'code': "Coupon code / URL",
            'pa': "Limit to pricing option",
            'unit_price': "Base price adjustment",
            'paygo_price': "PayGo price adjustment",
            '_access_period': "Access period override",
            '_tag_matches': "Override license tag matches",
            'access_end': "Fixed end override",
            '_description': "Optional description",
            'uses_max': "Maximum uses",
            'uses_current': "Current uses",
            'account_codes': "Limit to account codes",
            'enabled': "Enable coupon",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'code': "Code the user types in to apply this coupon, the URL name used "
                    "in a link, or both (case-insensitive, no spaces)<br>"
                    "Can only be set when coupon created; make a copy to change<br>",
            '_tag_matches': tag_code_help(
                    "Optionally override pricing option content.<br>"),
            'pa': "Tie coupon to a specific pricing option or...<br>"
                    "...leave blank for a global coupon, which requires users<br>"
                    "to select a pricing option when used.",
            'unit_price': "Leave blank to use pricing option default<br>"
                    "Enter 0 for free access<br>"
                    "Use < 1.00 for a percent discount on base price<br>"
                    "Use >= 1.00 for a specific base price",
            'paygo_price': "Leave blank to use pricing option default<br>"
                    "Enter 0 for free access<br>"
                    "Use < 1.00 for a percent discount on each PayGo increment<br>"
                    "Use >= 1.00 for a specific PayGo increment price",
            '_access_period': "Leave blank to use <b>pricing option</b> access period"
                    "<span id='help_access_period'></span>.<br>"
                    "You can set a specific access period (e.g., '2 weeks') or <br>"
                    "enter <b>perpetual</b> (or just 'p') to force a perpetual license.<br>"
                    "{help_license_pricing}",
            'access_end': "Leave blank to use pricing option settings.<br>"
                    "Or set a fixed expiration date for content access.<br>",
            '_description': "Optional description that overrides the default "
                    "display of of the pricing option description",
            'enabled': "This affects FUTURE coupon uses; "
                    "EXISTING licenses created with this coupon are not affected.",
            'coupon_expires': "Date the COUPON stops allowing new uses. "
                    "This does not affect the length of ACCESS the coupon provides. "
                    "Leave blank to keep coupon open indefinitely.",
            'account_codes': "Limit coupon to use by specific accounts by entering "
                    "a comma-delimited list of account codes.",
            'uses_max': "Number of times this coupon can be used. Leave blank for no limit.",
            'uses_current': "Total usages since the last time coupon's code was updated.",
            'history': "Significant changes to the coupon's history "
                    "(like changing price or max uses) are added here.",
            '_rules': "Add to or overwrite license rules.<br>"
                    "{help_license_rules}",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'code': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            '_tag_matches': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'uses_max': forms.NumberInput( attrs={'style': 'min-width: 12em;'} ),
            'uses_current': forms.NumberInput( attrs={'style': 'min-width: 12em;'} ),
            'account_codes': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            'history': forms.Textarea( attrs={'rows': 8, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            '_description': forms.Textarea( attrs=mc.UI_TEXTAREA_DEFAULT ),
            })

#--------------------------------------------------------------------

class ActiveFilter( mpListFilter ):
    """
    Active coupons are enabled and have a valid date
    """
    title = "State"
    parameter_name = 'state'
    def lookups( self, request, model_admin ):
        return [ ( 'active', "Active" ),
                 ( 'inactive', "Inactive" ),
                 ]
    def queryset( self, request, qs ):
        query = Coupon.is_active_Q()
        if self.value() == 'active':
            return qs.filter( query ).distinct()
        if self.value() == 'inactive':
            return qs.exclude( query ).distinct()

PAsFilter = mpListFilter.new( PA, u"Pricing option", 'pa_id' )

#--------------------------------------------------------------------

class CouponAdmin( BaseTenantAdmin ):
    form = CouponForm

    list_display = ( 'code', 'pa', 'enabled',
            'unit_price', '_access_period', 'tags',
            'uses_current', 'uses_max',
            'coupon_expires', 'access_end', 'account_codes', 'hist_modified' )
    list_editable = ( 'enabled', 'unit_price', '_access_period' )
    list_text_small = BaseTenantAdmin.list_text_small + (
            'available', 'enabled', 'tags',
            'uses_current', 'uses_max', 'coupon_expires',
            'access_end', 'pa', 'account_codes' )
    list_col_small = BaseTenantAdmin.list_col_small + (
            'available', 'enabled', 'uses_current', 'uses_max' )
    list_col_med = BaseTenantAdmin.list_col_med + (
            'code', 'pa', 'tags', 'unit_price', '_access_period',
            'coupon_expires', 'account_codes', 'access_end' )
    list_hide_med = BaseTenantAdmin.list_hide_med + (
            'access_end', 'account_codes' )

    list_filter = [ ActiveFilter, PAsFilter,
            'hist_modified', 'hist_created' ]
    list_filter_options = {
        'ActiveFilter': { 'default': 'active' },
        }

    search_fields = ( 'code', '_description', 'unit_price', 'account_codes' )

    readonly_fields = ( 'uses_current' ,)
    immutable_fields = ( 'code' ,)

    can_add_item_everywhere = True

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': [
                ('code', '_description'),
                ('pa', 'enabled'),
                ('unit_price', '_access_period'),
                ('uses_max', 'uses_current'),
                ]
            }),
        ("Additional options and history", {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('_tag_matches', 'coupon_expires'),
                ('account_codes', 'access_end'),
                ('hist_created', 'hist_modified'),
                ('history',),
                )
            }),
        ("Usage metering", {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('paygo_price',),
                ('unit_points', 'paygo_points'),
                ('unit_users', 'paygo_users'),
                ('unit_minutes', 'paygo_minutes'),
                ]
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                '_rules',
                'sandbox',
                )
            }),
        ]

    @property
    def can_copy( self ):
        return True

    def get_list_display( self, request ):
        user = request.user
        rv = list( super().get_list_display( request ) )
        if ActiveFilter.parameter_name in request.GET:
            rv.insert( 4, 'available' )
        if not user.access_high:
            rv.remove('access_end')
            rv.remove('account_codes')
        return rv

    def get_list_filter( self, request ):
        user = request.user
        rv = super().get_list_filter( request )
        if user.access_high:
            rv = self.list_insert( rv, ['coupon_expires', 'access_end'], 1 )
        return rv

    def tags( self, obj ):
        return obj.tag_matches
    tags.short_description = "License tags"

    def available( self, obj ):
        return obj.available
    available.short_description = "Available"
    available.boolean = True

root_admin.register( Coupon, CouponAdmin )


class CouponStaffAdmin( StaffAdminMixin, CouponAdmin ):
    pass

staff_admin.register( Coupon, CouponStaffAdmin )
