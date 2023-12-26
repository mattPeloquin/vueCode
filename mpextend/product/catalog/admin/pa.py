#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PA / Pricing option admin
"""
from django import forms
from django.conf import settings

from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.content.mpcontent.tags import tag_code_help

from ..models import PA
from ..models import Agreement
from .base_form import BaseCatalogFormMixin


class PAForm( BaseCatalogFormMixin, BaseModelForm ):
    class Meta:
        model = PA
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'sku': "SKU / URL",
            'agreement': "License type",
            '_access_period': "Access period",
            '_unit_price': "Base price",
            '_paygo_price': "PayGo price",
            'enabled': "Available for future use",
            '_tag_matches': "Match license tags",
            'access_end': "Fixed license expiration",
            'pa_expires': "Optional date to stop offering",
            'pa_starts': "Optional date to start offering",
            'visibility': "Who sees this pricing option?",
            'account_codes': "Limit to specific accounts",
            'control_apas': "Update existing licenses",
            '_rules': "License rules",
             })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'sku': "Unique code for links, searching and reporting "
                    "(no spaces or slashes).<br>",
            '_tag_matches': tag_code_help(),
            'agreement': "<span id='help_agreement_notes'>"
                    "License types define pricing structure and options.<br>"
                    "Optionally change the default license structure."
                    "</span>",
            '_access_period': "Calendar duration for content access.<br>"
                    "Leave blank for a <b>perpetual</b> license.<br>"
                    "Or customize the access period, for example: 10 min, 4 hours, "
                    "3 days, 2 weeks, 1 month, yearly, etc.<br>"
                    "{help_license_pricing}",
            '_unit_price': "Base price for an <b>access period</b>.<br>"
                    "<b>Subscriptions</b> charge this price each access period.<br>"
                    "Leave blank for free licenses or <b>backoffice</b> licenses "
                    "that are invoiced separately.<br>"
                    "{help_license_pricing}",
            '_paygo_price': "Optional Pay-as-you-Go (PayGo) usage metering.<br>"
                    "PayGo charges only accrue after <b>base price</b> metering "
                    "is consumed. Once base usage is exhausted access is suspended "
                    "unless PayGo pricing is set.<br>"
                    "The PayGo price is charged for each PayGo usage increment "
                    "beyond the base usage during an <b>access period</b>.<br>"
                    "{help_license_metering}",
            'enabled': "Turn off to remove this pricing option from FUTURE use.<br>"
                    "EXISTING licenses are not affected unless "
                    "<b>update existing</b> is checked.",
            'access_end': "Optionally set a fixed end date (does not affect "
                    "existing licenses unless <b>update existing</b> is checked).<br>"
                    "This end date overrides <b>access period</b> "
                    "and subscription settings.",
            '_description': "Text displayed during purchase process.<br>"
                    "Leave blank for automated text based on time and price.<br>"
                    "Optionally use these tags to include values:<br>"
                    "{{price}}, {{period}}, {{minutes}}, {{hours}}, {{days}}",
            '_name': "Optional short display name used on licensing screens.<br>"
                    "Defaults to the SKU if left blank",
            'control_apas': "Update existing licenses to match current "
                    "enabled, license tags, fixed end date, and metering settings.<br>"
                    "When off pricing option changes only affect new licenses.<br>",
            'visibility': "Optionally limit pricing option use to:<br>"
                    "EasyLink URL (not shown in popup)"
                    "Specific accounts (by account codes), "
                    "Backoffice staff",
            'account_codes': "If <b>specific accounts</b> is selected, "
                    "enter the account codes (comma delimited) that "
                    "have access to this pricing option.",
            'pa_starts': "Date when this pricing option becomes available<br>"
                    "Leave blank to make active immediately",
            'pa_expires': "Does NOT affect existing licenses.<br>"
                    "FUTURE licenses cannot be created after the date.<br>"
                    "Leave blank for no expiration.",
            '_rules': "Add to or overwrite license rules.<br>"
                    "{help_license_rules}",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'sku': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            '_name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            'account_codes': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            '_tag_matches': forms.Textarea( attrs=mc.UI_TEXTAREA_DEFAULT ),
            '_description': forms.Textarea( attrs=mc.UI_TEXTAREA_DEFAULT ),
            '_rules': CodeEditor( mode='yaml', theme='default', replace=False, rows=8 ),
            })

    no_prompt = forms.BooleanField( required=False,
            label="Apply without prompting",
            help_text="Apply this pricing option without prompting customer for "
                    "purchase options, sensing them directly to payment screen." )

    yaml_form_fields = BaseCatalogFormMixin.yaml_form_fields.copy()
    yaml_form_fields['_rules']['form_fields'].extend([
            '>>no_prompt',
            ])

#--------------------------------------------------------------------

class ActiveFilter( mpListFilter ):
    """
    An active PA is one that:
        - COULD BE USED to create a new APA
        - IS IN USE by and active APA
    """
    title = "State"
    parameter_name = 'state'
    def lookups( self, request, model_admin ):
        return [ ( 'active', "Active" ),
                 ( 'inactive', "Inactive" ),
                 ]
    def queryset( self, request, qs ):
        query = PA.available_Q() | PA.in_use_Q()
        if self.value() == 'active':
            return qs.filter( query ).distinct()
        if self.value() == 'inactive':
            return qs.exclude( query ).distinct()

class SubscriptionFilter( mpListFilter ):
    title = "Subscription"
    parameter_name = 'subscription'
    def lookups( self, request, model_admin ):
        return [ ( 'auto', "Subscription" ),
                 ( 'manual', "Manual renewal" ),
                 ( 'single', "Single use" ),
                 ]
    def queryset( self, request, qs ):
        auto = PA.is_subscription_Q() & PA.is_reusable_Q()
        if self.value() == 'auto':
            return qs.filter( auto ).distinct()
        if self.value() == 'manual':
            return qs.exclude( auto ).distinct()
        if self.value() == 'single':
            return qs.exclude( PA.is_reusable_Q() ).distinct()

AgreementFilter = mpListFilter.new( Agreement, u"License type", 'agreement_id' )

#--------------------------------------------------------------------

class PAAdminBase( BaseTenantAdmin ):
    form = PAForm

    list_display = ( 'sku', 'available', 'licenses',
            '_tag_matches', '_unit_price', '_access_period',
            'agreement', 'subscription', 'visibility', 'description',
            'metering', 'access_price', 'access_end', 'hist_modified' )
    list_display_links = ( 'sku' ,)
    list_editable = ( '_tag_matches', '_unit_price', '_access_period' )
    list_text_small = BaseTenantAdmin.list_text_small + (
            'available', 'visibility', 'licenses', 'description',
            'agreement', 'subscription', 'access_end',
            'metering', 'access_price' )
    list_col_large = BaseTenantAdmin.list_col_large + (
            '_tag_matches', )
    list_col_med = BaseTenantAdmin.list_col_med + (
            '_unit_price', '_access_period', 'available', 'visibility',
            'subscription', 'licenses', 'metering' )
    list_hide_med = BaseTenantAdmin.list_hide_med + (
            'agreement', 'visibility', 'access_end' )
    list_hide_small = BaseTenantAdmin.list_hide_small + (
            'licenses', 'metering', 'access_price' )

    list_filter = ( ActiveFilter, SubscriptionFilter, AgreementFilter,
            'visibility', 'enabled', 'control_apas',
            'hist_modified', 'hist_created' )
    list_filter_options = {
        'ActiveFilter': { 'default': 'active' },
        }

    search_fields = ( 'sku', '_name', '_description', '_tag_matches',
                        '_unit_price', 'account_codes' )

    filter_fk = dict( BaseTenantAdmin.filter_fk, **{
            'agreement': ( Agreement.objects, 'PROVIDER', ('enabled',True) ),
             })

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': [
                ('sku', 'agreement'),
                ('_tag_matches', '_description'),
                ('_unit_price', '_access_period'),
                ('visibility', 'auto_renew'),
                ('notes', 'enabled'),
                ]
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse',),
            'fields': (
                '_rules',
                'sandbox',
                )
            }),
        ]
    after_create_fieldsets = [
        (_("Usage metering"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse',),
            'fields': [
                ('_paygo_price',),
                ('unit_points', 'paygo_points'),
                ('unit_users', 'paygo_users'),
                ('unit_minutes', 'paygo_minutes'),
                ]
            }),
        (_("Additional options and history"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse',),
            'fields': [
                ('no_prompt', 'is_trial'),
                ('active_users_max', 'access_end'),
                ('_name', 'initial_price'),
                ('account_codes', 'control_apas',),
                ('pa_starts', 'pa_expires'),
                ('hist_created', 'hist_modified'),
                ]
            }),
        ]

    def get_list_display( self, request ):
        rv = list( super().get_list_display( request ) )
        if not request.user.access_high:
            rv.remove('visibility')
            rv.remove('access_price')
            rv.remove('access_end')
        if not request.user.access_all:
            rv.remove('metering')
        return rv

    def available( self, obj ):
        return obj.available
    available.short_description = "Currently available"
    available.boolean = True

    def licenses( self, obj ):
        return obj.active_apa_count
    licenses.short_description = "Active licenses"

    def access_price( self, obj ):
        return obj.access_price
    access_price.short_description = "Access price"

    def subscription( self, obj ):
        return obj.is_subscription
    subscription.short_description = "Subscription"
    subscription.boolean = True

    def metering( self, obj ):
        return obj.metering_desc
    metering.short_description = "Metering"

    def description( self, obj ):
        return obj.description
    description.short_description = "Display text"

#--------------------------------------------------------------------

class PaStaffAdmin( StaffAdminMixin, PAAdminBase ):
    helptext_changeform_add = _("Create a new pricing option based on a "
            "license type.<br>"
            "Additional options can be modified after creation.")

    # Lower limit since there are many editables and shouldn't be too many PAs
    list_per_page = PAAdminBase.list_per_page // 2

staff_admin.register( PA, PaStaffAdmin )


class PaRootAdmin( PAAdminBase ):
    pass

root_admin.register( PA, PaRootAdmin )
