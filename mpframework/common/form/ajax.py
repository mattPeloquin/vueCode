#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Ajax form support
"""

from .. import log
from ..api import respond_api_call


def respond_ajax_form( request, **kwargs ):
    """
    Shared handling for creating the response for Ajax submission of forms
    """
    def handler( payload ):
        rv = kwargs
        log.debug("AJAX form save: %s", rv)
        return rv
    return respond_api_call( request, handler )


def respond_ajax_model_form( request, obj ):
    """
    Add specific support for model forms
    This should be called AFTER the model is saved
    """
    def handler( payload ):

        # Add file updates so they can be refreshed on client
        # The names of any files must be updated to match what was saved
        rv = payload.get( 'post_FILES', {} )
        for field, _file in rv.items():
            saved_file = getattr( obj, field, None )
            if saved_file:
                rv[ field ] = saved_file.name

        # Success message
        opts = obj.__class__._meta
        msg = '{} "{}" saved, you may continue editing'.format(
                        opts.verbose_name, obj )
        rv['msg'] = msg

        log.debug("AJAX model form save: %s -> %s", request.mpipname, rv)
        return rv
    return respond_api_call( request, handler )
