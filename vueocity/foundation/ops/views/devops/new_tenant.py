#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test scree for new tenant
"""
from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views.decorators.debug import sensitive_post_parameters

from mpframework.common import log
from mpframework.common.form import BaseForm
from mpframework.common.view import root_only
from mpframework.common.view import ssl_required
from mpframework.common.logging.utils import remove_secrets
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.foundation.tenant.models.provider import Provider
from mpframework.foundation.tenant.models.sandbox_host import SandboxHost


@root_only
class NewTenantForm( BaseForm ):

    subdomain = forms.CharField()
    email = forms.EmailField( widget=forms.EmailInput() )
    password = forms.CharField( widget=forms.PasswordInput() )

    def clean_subdomain( self ):
        subdomain = self.cleaned_data.get('subdomain')
        subdomain = Sandbox.objects.subdomain_ok( subdomain )
        if not subdomain:
            raise forms.ValidationError("Subdomain in use")
        return subdomain.lower()

@ssl_required
@sensitive_post_parameters()
def new_tenant( request ):
    """
    Testing support for adding a new provider and default sandbox
    """
    sandbox = request.sandbox
    form = NewTenantForm()
    if request.method == "POST":
        form = NewTenantForm( data=request.POST )
        if form.is_valid():
            log.info("NEW TENANT: %s-> %s", request.mpipname, remove_secrets(request.POST))
            name = form.cleaned_data['subdomain']
            provider = Provider.objects.create_obj( name=name, system_name=name )
            sandbox = Sandbox.objects.create_obj( _provider=provider, subdomain=name )
            SandboxHost.objects.create_obj( sandbox=sandbox, main=True,
                                 _host_name='{}.{}'.format( name, settings.MP_ROOT['HOST'] ) )
            return HttpResponseRedirect( sandbox.portal_url() )

    return TemplateResponse( request, 'root/test/new_tenant.html', {
                'new_tenant_form': form,
                })
