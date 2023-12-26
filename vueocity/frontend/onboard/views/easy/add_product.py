#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    EasyVue add product

    This screen collects information that is used to create several models
    that represent a product.
"""
from django import forms
from django.conf import settings
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.utils.paths import path_extension
from mpframework.common.utils.strings import make_tag
from mpframework.common.form import BaseForm
from mpframework.common.form import parsleyfy
from mpframework.common.form import mpFileFormField
from mpframework.common.form import mpImageFormField
from mpframework.common.view import staff_required
from mpframework.content.mpcontent.models import ProtectedFile
from mpextend.content.mpcontent.models import LmsItem
from mpextend.content.mpcontent.models import Video
from mpextend.product.catalog.models import Agreement
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon


@parsleyfy
class EasyAddProductForm( BaseForm ):
    """
    Unlike most forms that create models, this form is not a model form since
    it's field values will be used across several models.
    This means the form needs to manage file data for files on its own rather
    than relying on the model's file fields.
    """
    content_file = mpFileFormField( required=True, direct=True, protected=True )
    image = mpImageFormField( required=False, direct=False )
    name = forms.CharField( required=True,
                widget=forms.TextInput(attrs={'size': '64'}) )
    billing = forms.CharField( required=False )
    price = forms.DecimalField( required=True, max_digits=6, decimal_places=2 )
    trial_min = forms.IntegerField( required=False )
    coupon_code = forms.CharField( required=False )
    coupon_price = forms.DecimalField( required=False, max_digits=6,
                decimal_places=2 )


@staff_required
def easy_add_product( request ):
    """
    Create the necessary content and catalog items from add product form
    HACK - Assumes specific agreement types in data
    """
    if 'GET' == request.method:
        form = EasyAddProductForm()

    elif 'POST' == request.method:
        log.info2("EasyAdd Product: %s", request.mpipname)

        form = EasyAddProductForm( request.POST, request.FILES )
        if not form.is_valid():
            log.debug("EasyAdd Product invalid form: %s -> %s",
                            form.errors, form.cleaned_data)
        else:
            sandbox = request.sandbox

            # Create tag and SKU from name, but make them different to
            # avoid confusion about them being the same thing
            name = form.cleaned_data['name']
            tag = make_tag( name, max_len=24 )
            sku = make_tag( name, under=True, lower=True, max_len=24 )

             # Make the appropriate content item based on uploaded file
            _create_content( form.cleaned_data['content_file'],
                             sandbox=sandbox, name=name, tag=tag,
                             image1=form.cleaned_data['image'] )

            # Create main PA using agreement that matches billing cycle
            # HACK - tied to existing agreement names
            agreements = list( Agreement.objects.filter( provider_optional=None ) )
            price = form.cleaned_data['price']
            billing = form.cleaned_data['billing']
            if price:
                if billing == 'monthly':
                    agreement = next( a for a in agreements if a.name == 'User seat subscription' )
                    access_period = 'month'
                else:
                    agreement = next( a for a in agreements if a.name == 'User seat purchase' )
                    access_period = 'year'
                pa = PA.objects.create_obj( sandbox=sandbox,
                            agreement=agreement, _access_period=access_period,
                            sku=sku, _unit_price=price, _tag_matches=tag )

                # Create free trial
                trial_min = form.cleaned_data['trial_min']
                if trial_min:
                    agreement = next( a for a in agreements if a.name == 'User seat trial' )
                    PA.objects.create_obj( sandbox=sandbox,
                            agreement=agreement, _access_period=trial_min + " min",
                            sku=sku + "_trial", _tag_matches=tag )

                # Create coupon
                coupon_code = form.cleaned_data['coupon_code']
                if coupon_code:
                    Coupon.objects.create_obj( sandbox=sandbox, code=coupon_code, pa=pa,
                                               _unit_price=form.cleaned_data['coupon_price'] )

            if 'add_another' in request.POST:
                form = EasyAddProductForm()
            else:
                return HttpResponseRedirect( sandbox.portal_url() )

    request.is_page_staff = True
    return TemplateResponse( request, 'easy/add_product.html', {
                'form': form,
                })

def _create_content( file, **kwargs ):
    """
    Create content from a file, based on the file type.
    The content file and its image may be either a string (for direct uploads)
    or a Django file data object (for posted uploads)
    """
    direct = isinstance( file, str )
    filename = file if direct else file.name
    file_ext = path_extension( filename )
    if file_ext in ['zip']:
        item = LmsItem.objects.create_obj( file_name=file, **kwargs )
    if file_ext in settings.MP_FILE['VIDEO_TYPES']:
        item = Video.objects.create_obj( file_med=file, **kwargs )
    else:
        item = ProtectedFile.objects.create_obj( content_file=file, **kwargs )
    return item
