#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Default sandbox portal code
"""
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from ..bootstrap import bootstrap_dict_embed
from ..bootstrap import bootstrap_dict_content_timewin
from ..bootstrap import bootstrap_dict_user_timewin
from ..bootstrap import bootstrap_dict_nocache


@ensure_csrf_cookie
def portal_view( request, **kwargs ):
    return sandbox_portal( request, portal_url=None, **kwargs )

def sandbox_portal( request, **kwargs ):
    """
    Returns HTTP response for portal requests.
    Handle selection of portal template, setting up context, tool posts,
    and any special routing or actions based on extra information in URL.
    """
    # Special case the root portal
    if request.sandbox.is_root:
        return HttpResponseRedirect(
                    reverse('root_admin:tenant_provider_changelist') )

    # Note portal page for convenience
    request.is_portal = True

    # Update current context based on any extra information
    context = _init_context( request, **kwargs )

    # Get frame and update context with any frame values
    frame_template = _skin_frame( request, context )

    return TemplateResponse( request, frame_template, context )

def _init_context( request, **kwargs ):
    """
    Setup initial portal context
    """
    sandbox = request.sandbox
    context = kwargs.pop( 'context', {} )

    # If a different theme or frame is requested, load it into the request
    portal_opts = {}
    theme_id = kwargs.pop( 'theme_id', None )
    frame_id = kwargs.pop( 'frame_id', None )
    if theme_id:
        request.skin.set_theme( theme_id )
        portal_opts['theme_id'] = theme_id
    if frame_id:
        request.skin.set_frame( frame_id )
        portal_opts['frame_id'] = frame_id

    # Change url_portal if needed to keep site anchored to theme or frame
    # This may already be set with an existing sticky url
    url_portal_args = context.get( 'url_portal_args', {} )
    if url_portal_args:
        url_portal_args['url_kwargs'].update( portal_opts )
        context['url_portal_kwargs'] = url_portal_args['url_kwargs']
    elif portal_opts:
        url_portal_args['url_name'] = 'portal_theme' if theme_id else 'portal_frame'
        url_portal_args['url_kwargs'] = portal_opts
    if url_portal_args:
        context['url_portal'] = reverse( url_portal_args['url_name'],
                    kwargs=url_portal_args['url_kwargs'] )

    # Uncached and template-cached groups of bootstrap data
    if( not sandbox.options['bootstrap.embed_in_link'] ):
        context.update({
            'bootstrap_data_embed': lambda: bootstrap_dict_embed( request ),
            })

    # Load bootstrap data directly into page based on options
    if( sandbox.options['bootstrap.content_data_in_page'] ):
        context.update({
            'bootstrap_data_content': lambda: bootstrap_dict_content_timewin( request ),
            })
    if sandbox.options['bootstrap.user_data_in_page']:
        context.update({
            'bootstrap_data_user': lambda: bootstrap_dict_user_timewin( request ),
            })
    if sandbox.options['bootstrap.nocache_data_in_page']:
        context.update({
            'bootstrap_data_nocache': lambda: bootstrap_dict_nocache( request ),
            })

    return context

def _skin_frame( request, context ):
    """
    Update context with any frame values and return path to portal frame
    """
    skin = request.skin
    frame_context = skin.frame.structure_context( skin )
    frame_template = frame_context['frame_template']

    # Add the frame-specific context
    context['request_frame'] = frame_context
    context['request_frame']['name'] = frame_template.replace( '.html', '' )

    return 'portal/frames/{}'.format( frame_template )
