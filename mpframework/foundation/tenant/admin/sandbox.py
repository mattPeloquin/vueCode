#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sandbox admin screens

    FUTURE - support for staff to change subdomain, sync with SandboxHost
"""
from copy import deepcopy
from django import forms
from django.urls import reverse

from mpframework.common import _
from mpframework.common.aws import ses
from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.form import mpHtmlFieldFormMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.ops.admin import FieldChangeMixin
from mpframework.frontend.sitebuilder.models import Theme
from mpframework.frontend.sitebuilder.admin.base_theme import ThemeFormBase
from mpframework.frontend.sitebuilder.admin.base_theme import ThemeAdminBase

from ..models.sandbox import Sandbox
from ..models.sandbox_host import SandboxHost
from . import TabularInlineNoTenancy


class SandboxForm( mpHtmlFieldFormMixin, ThemeFormBase ):
    sanitize_html_fields = ( 'summary', 'intro_html', 'login_html',
            'footer_html', 'terms_html' )
    class Meta:
        model = Sandbox
        exclude = ()

        labels = dict( ThemeFormBase.Meta.labels, **{
            'timezone': "Time zone",
            'email_support': "Customer support email",
            'theme': "Site theme",
            'hero_image': "Hero image",
            'hero_video': "Hero video",
            'hero_image2': "Login hero image",
            'icon': "Site icon",
            'logo': "Site logo",
            'summary': "Summary text",
            'intro_html': "Summary HTML",
            'home_html': "Home page HTML",
            'login_html': "Signup HTML",
            'footer_html': "Site footer HTML",
            'terms_html': "Additional terms of use",
            'html1': "Additional HTML #1",
            'html2': "Additional HTML #2",
            '_email_staff': "Staff email",
            'notify_level': "Notification level",
            'delivery_mode': "Content protection level",
            'options': "Site config",
            'snippet_head': "Custom HTML added to head",
            'snippet_body': "Custom HTML added to body",
            'taxes': "Add taxes",
            })
        help_texts = dict( ThemeFormBase.Meta.help_texts, **{
            'name': "Main public name for this site, used on pages, emails, "
                    "browser tabs, etc.",
            'timezone': "Timezone used to display times to users and staff "
                    "(doesn't affect how times are stored)",
            'email_support': "<b>Address for emails from this site.</b><br>"
                    "Must be a valid email or distribution list.<br>"
                    "<b>When changed Amazon will send a verification email you MUST "
                    "respond to before email sending will work.</b>",
            '_email_staff': "Notification emails are sent TO this address (user events, "
                    "purchases, etc).<br>"
                    "Leave blank to use the customer support email.",
            'notify_level': "Select the level of notification emails to send",
            'theme': "Choose your site's base theme. Themes bring together "
                    "layout and style options to create a distinct user experience.<br>"
                    "Optionally customize the base theme using the options below.",
            'summary': "Brief description of the site, used for home page "
                    "and external services like Facebook.",
            'hero_image': "Large image displayed under text on site home page.<br>"
                    "Image sizing is controlled by the hero size setting. The image will "
                    "zoom and crop to fit different screen sizes. It is best to upload the "
                    "aspect ratio you'd like to display.",
            'hero_video': "Optional video displayed under text on site home page.<br>"
                    "Upload a short video that will loop without sound.<br>"
                    "The hero image will be used as a poster.",
            'hero_image2': "Hero image used instead of main hero image for sign-in pages",
            'icon': "For browser tabs, footer, etc. A transparent background "
                    "gives best results.",
            'logo': "Optional image used to represent the site externally "
                    "for Facebook, etc. (leave blank to use the site icon).",
            'delivery_mode': "Adjust the level of protection used when users access content",
            'options': "Site-specific advanced configuration.<br>"
                    "{help_site_options}",
            'intro_html': "Optional HTML displayed instead of summary text on home page, "
                    "usually over the hero image.",
            'home_html': "Optional HTML displayed on some home page layouts below the "
                    "summary HTML.",
            'login_html': "Optional HTML displayed instead of the summary on the "
                    "login screen.",
            'footer_html': "HTML added to bottom of every page.",
            'html1': "HTML that can be injected into any template with {{ site.html1 }}",
            'html2': "HTML that can be injected into any template with {{ site.html2 }}",
            'snippet_head': "HTML added to site pages in the head tag.",
            'snippet_body': "HTML added to site pages in the body tag. "
                    "This is usually the best place to add Javascript.<br>"
                    "jQuery is loaded and available here.",
            'taxes': "Add postal code ranges which should be charged taxes.<br>"
                    "{help_site_taxes}",
            'terms_html': "Add custom terms of use, which are shown in "
                    "addition to Vueocity usage terms",
            'subdomain': "Internal system name for default URL host and S3 storage",
            '_resource_path': "Path to resources, added to the provider resource_path."
                    "Keep in sync with S3 folders. Leave blank to default to subdomain",
            })
        widgets = dict( ThemeFormBase.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            'email_support': forms.EmailInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            '_email_staff': forms.EmailInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'summary': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            'intro_html': HtmlEditor( rows=12 ),
            'home_html': HtmlEditor( rows=12 ),
            'login_html': HtmlEditor( rows=12 ),
            'footer_html': HtmlEditor( rows=12 ),
            'terms_html': HtmlEditor( rows=32 ),
            'html1': HtmlEditor( rows=24 ),
            'html2': HtmlEditor( rows=24 ),
            'snippet_head': CodeEditor( rows=24 ),
            'snippet_body': CodeEditor( rows=24 ),
            'taxes': CodeEditor( mode='yaml', theme='default', rows=16 ),
            'options': CodeEditor( mode='yaml', theme='default', rows=16 ),
            '_policy': CodeEditor( mode='yaml', theme='default', rows=16 ),
            })

    google = forms.CharField( required=False,
            label="Google GTM or UA",
            help_text="To track site activity with Google Analytics enter either "
                "your Google Tag Manager ID or your Google Universal Analytics ID." )
    twitter = forms.CharField( required=False,
            label="Twitter site handle",
            help_text="Optional '@' handle for the Twitter account to associate "
                "with this site." )
    web_url = forms.CharField( required=False,
            label="External website",
            help_text="Link to external website when footer or banner is clicked." )
    copyright = forms.CharField( required=False,
            label="Copyright name",
            help_text="Name displayed next to content copyright, defaults to site name." )
    private_portal = forms.BooleanField( required=False,
            label="Make portals private",
            help_text="Require users to create an account "
                "to see this site's main portal or any content pages.<br>"
                "Leave unchecked for storefronts and other cases where visitors "
                "can browse content descriptions." )
    verify_new_users = forms.BooleanField( required=False,
            label="New users must verify email",
            help_text="Require users to verify new emails.<br>"
                "This ensures emails are valid and prevents abusing free "
                "trials, but adds an extra step to user registration." )
    user_create_code = forms.CharField( required=False,
            label="User create code",
            help_text="Optional code required for new user creation.<br>"
                "Leave blank to allow anyone to make a user account. This is "
                "recommended as they still need licenses to access content." )
    no_text_selection = forms.BooleanField( required=False,
            label="Prevent user text selection",
            help_text="By default portals allow users to select and copy "
                "descriptive text. Select this to prevent users "
                "(but not staff) from easily selecting text." )

    yaml_form_fields = ThemeFormBase.yaml_form_fields.copy()
    yaml_form_fields.update({
        '_policy': {
            'upstream_getter': 'policy',
            'form_fields': [
                '>>google',
                'private_portal', 'verify_new_users', 'user_create_code',
                ]
            },
        'options': {
            'form_fields': [
                'no_text_selection', 'twitter', 'web_url', 'copyright',
                ]
            },
        })

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        if self.fields.get('theme'):
            self.fields['theme'].empty_label = u"No theme"


class SandboxHostAdminInline( TabularInlineNoTenancy ):
    model = SandboxHost
    verbose_name_plural = u"Valid hosts"
    fields = ( '_host_name', 'main', 'https', 'redirect_to_main' )
    classes = ( 'mp_collapse' ,)


class SandboxAdminBase( FieldChangeMixin, mpHtmlFieldFormMixin, ThemeAdminBase ):
    form = SandboxForm
    sees_sandboxes_required = True

    list_filter = ( 'frame_site', '_default_viewer', '_login' )
    search_fields = ( 'name', 'subdomain', '_resource_path', 'email_support', '_email_staff',
                      '_provider__name' )

    changed_fields_to_save = ThemeAdminBase.changed_fields_to_save + (
            'name', 'summary', 'options', 'snippet_head', 'snippet_body',
            'intro_html', 'login_html', 'footer_html', 'terms_html' )

    filter_fk = dict( ThemeAdminBase.filter_fk, **{
            'theme': ( Theme.objects, 'PROVIDER_OPTIONAL_REDUCE_NAME' ),
             })

    fieldsets_default = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': [
                ('name','email_support'),
                ('private_portal','timezone'),
                ('verify_new_users','user_create_code'),
                ('google','twitter'),
                ]
            }),
        (_("Descriptions"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'summary',
                'intro_html',
                'home_html',
                'login_html',
                ('web_url','copyright'),
                'footer_html',
                )
            }),
        (_("Site options"), {
            'mp_staff_level': 'access_med',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('_email_staff','notify_level'),
                ('delivery_mode','no_text_selection'),
                'terms_html',
                'taxes',
                )
            }),
        (_("Advanced options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'options',
                'html1',
                'html2',
                )
            }),
        (_("SandboxHostAdminInline"), {    # Name must match inline for staff level removal
            'mp_staff_level': 'access_root_menu',
            'classes': ( 'mp_placeholder hosts-group' ,),
            'fields' : (),
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                '_provider',
                ('subdomain','_resource_path'),
                ('hist_created','hist_modified'),
                '_policy',
                )
            }),
        ]

    fieldsets_custom = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                'theme',
                )
            }),
        (_("Site visuals"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'icon',
                ('hero_image','hero_video'),
                ('hero_image2','logo'),
                ]
            }),
        (_("Change theme styling"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse mp_closed',),
            'fields': ThemeAdminBase.fieldset_theme_style,
            }),
        (_("Change theme layout"), {
            'mp_staff_level': 'access_med',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'frame_site',
                ] + ThemeAdminBase.fieldset_theme_layout,
            }),
        (_("Change theme options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('frame_tree','frame_item'),
                ] + ThemeAdminBase.fieldset_theme_options,
            }),
        (_("Content defaults"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'portal__item_order',
                ('portal__no_play_next','portal__hide_empty'),

                )
            }),
        (_("Advanced options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'sb_options',
                )
            }),
        ]

    fieldsets_code = [
        (_("Add CSS"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse',),
            'fields': (
                'css_head',
                )
            }),
        (_("Add HTML"), {
            'mp_staff_level': 'access_med',
            'classes': ('mp_collapse',),
            'fields': (
                'snippet_head',
                'snippet_body',
                )
            }),
        ]

    def response_url( self, request ):
        """
        Always send back to portal after any sandbox change since there's few
        scenarios where we want to show changelist, and most sandbox changes
        are related to having an impact on the portal.
        """
        return reverse('portal_view')

    def has_add_permission( self, request ):
        return request.sandbox.policy.get('create_site') or request.user.is_root

    def save_model( self, request, obj, form, change ):
        super().save_model( request, obj, form, change )

        # Update SES email verification
        if not change or 'email_support' in form.changed_data:
            ses.verify_email( obj.email_support )

    def private_portal( self, obj ):
        return bool( obj.policy['private_portal'] )
    private_portal.short_description = "Private"
    private_portal.boolean = True

    def user_create_code( self, obj ):
        return bool( obj.policy['user_create_code'] )
    user_create_code.short_description = "Create code"
    user_create_code.boolean = True

    def verify_new_users( self, obj ):
        return bool( obj.policy['verify_new_users'] )
    verify_new_users.short_description = "Verify users"
    verify_new_users.boolean = True

#--------------------------------------------------------------------

class SandboxStaffAdmin( StaffAdminMixin, SandboxAdminBase ):
    """
    The main user sandbox editing screen
    """
    inlines = ( SandboxHostAdminInline ,)
    list_display = ( '__str__', 'theme', '_email_staff', 'email_support', 'private_portal',
                     'verify_new_users', 'user_create_code', 'delivery_mode' )
    list_display_links = ( '__str__' ,)
    ordering = ( 'name' ,)
    fieldsets = SandboxAdminBase.fieldsets_default

staff_admin.register( Sandbox, SandboxStaffAdmin )

class SandboxStaffAdmin_Custom( StaffAdminMixin, SandboxAdminBase ):
    """
    Place customization stuff under separate screen
    Changelist should never be visible
    """
    fieldsets = SandboxAdminBase.fieldsets_custom
    hide_notes = True

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust fields based on user level
        """
        rv = super().get_fieldsets( request, obj )
        images = rv[1][1]['fields']
        if not request.user.access_high:
            images.remove( ('hero_image2','logo') )
        return rv

class SandboxCustom( Sandbox ):
    class Meta:
        proxy = True
        verbose_name = u"Site customization"

staff_admin.register( SandboxCustom, SandboxStaffAdmin_Custom )

class SandboxStaffAdmin_Code( StaffAdminMixin, SandboxAdminBase ):
    """
    Sitebuilder code-additions in separate screen
    Changelist should never be visible
    """
    fieldsets = SandboxAdminBase.fieldsets_code
    hide_notes = True

class SandboxSitebuilder( Sandbox ):
    class Meta:
        proxy = True
        verbose_name = u"SiteBuilder code"

staff_admin.register( SandboxSitebuilder, SandboxStaffAdmin_Code )

#--------------------------------------------------------------------

class SandboxRootAdmin( SandboxAdminBase ):

    inlines = ( SandboxHostAdminInline ,)
    list_display = ( '_provider', 'subdomain', '_resource_path', '_email_staff', 'name',
                'verify_new_users', 'frame_site', 'private_portal',
                'theme', '_style', '_color', '_font', '_mixin',
                'user_create_code', '_policy' )
    list_filter = ( 'frame_site', 'theme', '_font', '_style', '_color', '_mixin' )
    list_display_links = ( 'subdomain', '_resource_path' )

    fieldsets = deepcopy( SandboxAdminBase.fieldsets_default +
                          SandboxAdminBase.fieldsets_custom +
                          SandboxAdminBase.fieldsets_code )

root_admin.register( Sandbox, SandboxRootAdmin )
