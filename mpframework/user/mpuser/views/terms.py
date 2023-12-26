#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Accept terms form view
"""
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.view import login_required
from mpframework.common.form import BaseModelForm

from ..models import mpUser


class AcceptTermsForm( BaseModelForm ):
    """
    Although this form doesn't directly represent model fields, using
    it as ModelForm to emphasize use of mpUser model for updating
    acceptance text
    """
    class Meta:
        model = mpUser
        fields = ()

    accepted = forms.BooleanField( required=True )

    def save( self, commit=True ):
        """
        Note the acceptance
        """
        if commit:
            acceptance_text = u"Accept Screen Select: {}-{}".format( self.instance.email, now() )
            log.info("Saving user acceptance info: %s", acceptance_text)
            self.instance.init_terms = acceptance_text
            self.instance.save()

@login_required
def accept_terms( request, **kwargs ):
    """
    Present terms to the user for acceptance, once accepted go to portal.
    Path may include extra info info needs to be preserved.
    """
    ename = kwargs.get('ename')
    evalue = kwargs.get('evalue')
    log.debug2("View accept_terms: %s, extra(%s, %s)", request.mpname, ename, evalue)

    # If user has accepted, note in DB and redirect to default portal
    if request.method == "POST":
        form = AcceptTermsForm( request.POST, instance=request.user )
        if form.is_valid():
            form.save()
            return HttpResponseRedirect( request.sandbox.portal_url( ename, evalue ) )

    # Otherwise display the acceptance screen
    # The url for form submission needs to be fixed up to include the extra info
    url = ( reverse('terms_accept') if not ename else
            reverse( 'terms_accept_extra', kwargs={ 'ename': ename, 'evalue': evalue } )
                           )
    return TemplateResponse( request, 'user/login/accept_terms.html', {
                                'accept_terms_url': url,
                                'form': AcceptTermsForm( instance=request.user ),
                                })
