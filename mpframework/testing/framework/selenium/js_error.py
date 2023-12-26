#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Detection of JS errors during Selenium runs
"""

from functools import wraps

from mpframework.common import log

from .. import mpTestingException


class JavascriptException( mpTestingException ):
    pass


def _raise_if_js_error( sln ):
    # HACK - hard-coded name inserted into page of error
    body = sln.find_element_by_css_selector("body")
    js_error = body.get_attribute("JS-ERROR")
    if js_error:
        log.error("|  JAVASCRIPT ERROR -- STOPPING TESTS\n%s", js_error)
        raise JavascriptException( js_error )


def stop_js_error( fn ):
    """
    Decorator to check JS errors before and after test case member functions
    """
    @wraps( fn )
    def wrapper( self, *args, **kwargs ):
        _raise_if_js_error( self.sln )
        rv = fn( self, *args, **kwargs )
        _raise_if_js_error( self.sln )
        return rv
    return wrapper


