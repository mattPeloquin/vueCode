#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    EasyVue Sandbox floating tool support

    Many Sandbox adjustments require full refreshes, so the tool is a form
    changes are posted to, instead of ajax.
"""
from django import forms
from django.http import HttpResponseRedirect

from mpframework.common import _
from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.view import staff_required
from mpframework.common.form import BaseModelForm
from mpframework.common.form import respond_ajax_model_form
from mpframework.foundation.tenant.query_filter import tenant_filter_form_fk
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.common.cache.template import template_no_page_cache
from mpframework.frontend.sitebuilder.models import Theme
from mpframework.frontend.sitebuilder.models import Frame
from mpframework.frontend.sitebuilder.models import TemplateCustom
from mpframework.frontend.portal.views import sandbox_portal


USE_THEME = _("Use theme")


class EasySandboxForm( BaseModelForm ):
    class Meta:
        model = Sandbox
        fields = ( 'theme', 'frame_site', '_style', '_mixin', '_font', '_color',
                'icon', 'hero_image', 'hero_video',
                'name', 'summary', 'timezone', 'email_support',
                )
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'name': forms.TextInput( attrs={'size': mc.CHAR_LEN_UI_SHORT } ),
            'summary': forms.Textarea( attrs=mc.UI_TEXTAREA_SMALL ),
            })

    def __init__( self, request, **kwargs ):
        sandbox = request.sandbox
        provider = sandbox.provider
        super().__init__( instance=sandbox, **kwargs )

        # Cut the select options down to appropriate tenancy and subsets
        self.fields['theme'].queryset = tenant_filter_form_fk( sandbox, provider,
                Theme.objects, 'PROVIDER_OPTIONAL_REDUCE_NAME' )
        self.fields['frame_site'].queryset = tenant_filter_form_fk( sandbox, provider,
                Frame.objects, 'PROVIDER_OPTIONAL', frame_type='P' )
        accessQ = TemplateCustom.has_access_Q( request.user.staff_level )
        self.fields['_style'].queryset = tenant_filter_form_fk( sandbox, provider,
                TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                template_type='B', Q=accessQ )
        self.fields['_mixin'].queryset = tenant_filter_form_fk( sandbox, provider,
                TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                template_type='D', Q=accessQ )
        self.fields['_font'].queryset = tenant_filter_form_fk( sandbox, provider,
                TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                template_type='A', Q=accessQ )
        self.fields['_color'].queryset = tenant_filter_form_fk( sandbox, provider,
                TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                template_type='C', Q=accessQ )

        # Don't allow blank choices when using the sandbox tool
        self.fields['theme'].empty_label = None
        self.fields['frame_site'].empty_label = USE_THEME
        self.fields['_font'].empty_label = USE_THEME
        self.fields['_style'].empty_label = USE_THEME
        self.fields['_mixin'].empty_label = USE_THEME
        self.fields['_color'].empty_label = USE_THEME

@staff_required
@template_no_page_cache
def easy_sandbox( request ):
    """
    Start the sandbox tool with a get, and then handle posts from it
    Since this is always shown from portal, it is implemented as a separate
    url that loads the portal but adds the sandbox tool form to context.
    """
    sandbox = request.sandbox
    form = None
    if 'POST' == request.method:

        if 'done_sandbox' in request.POST:
            return HttpResponseRedirect( sandbox.portal_url() )

        log.debug("Sandbox tool: %s -> %s", request.mpname, request.POST)
        form = EasySandboxForm( request, data=request.POST, files=request.FILES )
        if form.is_valid():
            form.save()
            form = None
        else:
            log.info("Invalid EasySandbox form: %s -> %s", request.mpname, form.data)

        if request.is_api:
            return respond_ajax_model_form( request, sandbox )

    if form is None:
        form = EasySandboxForm( request )

    return sandbox_portal( request, context={
                'sandbox_tool': form,
                'submit_url': request.path,
                })
