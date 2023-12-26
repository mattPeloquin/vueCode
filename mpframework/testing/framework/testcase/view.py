#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared view test case code
"""
import re
import json
from django.conf import settings
from django.urls import reverse
from django.contrib import admin

from mpframework.common.utils.strings import safe_unicode
from mpframework.common.utils.http import get_url_list

from .unit import UnitTestCase


class ViewTestCase( UnitTestCase ):
    """
    Provides view test utilities
    Includes introspection to find URLs defined in Django patterns
    and admin and do basic smoke testing on them
    This introspection can be a bit messy because the url structure
    doesn't always line up on app boundaries, so cheat in favor of
    checking the same urls more than once if necessary.
    """

    # Can't load MPF urls at start because it triggers admin
    # autodiscovery, so load lazily and cache
    mp_urls = None

    @classmethod
    def setUpClass( cls ):
        super().setUpClass()

        # Load admin to get admin urls
        admin.autodiscover()

    def _request_and_response( self, cmd, url, **kwargs ):
        """
        Get fully formed request and response for the given url

        Django's TestCase runs a fake HTTP request through middleware and then
        hands to views for processing. This returns an HTTP request dict vs. a
        middleware request object.
        """

        # Limit on expected redirects to satisfy the request
        redirects = kwargs.get('redirects')

        # Make fake HTTP request, with added host and data
        http_args = {
            'follow': bool(redirects),
            'data': kwargs.get('data'),
            'HTTP_HOST': self.host_url,
            }
        if kwargs.get('ajax'):
            http_args.update({ 'HTTP_X_REQUESTED_WITH' : 'XMLHttpRequest' })

        # Add testing info the request
        # This can only be access if MP_TESTING is true
        inject_text = ''
        success_text = kwargs.get('success_text')
        if success_text is not False:
            inject_text = None if success_text else "TEST_success_text:{}".format( url )
            success_text = success_text or inject_text
        self.client.handler.inject_mptest({
            'fail': kwargs.get('fail'),
            'current_user': self.current_user,
            'inject_text': inject_text,
            'success_text':success_text,
            })

        # Get the response and request from the test handler
        command_method = getattr( self.client, cmd )
        response = command_method( url, **http_args )
        request = self.client.handler.get_request()

        request.uri = "LOCALTEST/{}".format( request.path )
        return request, response

    def post_url( self, url, data=None, **kwargs ):
        return self.get_url( url, data, **kwargs )

    def get_url( self, url, data=None, must_exist=True, success_text=None, fail=False,
                  redirects=0, login_redirect=False, no_host=False ):
        """
        MAIN VIEW TESTER
        This is for testing view logic, NOT that a URL exists, since
        the URLs are generated through introspection there will be cases
        where assumptions used generate the URL create non-existent ones.
        The success text will by default be the page footer of the sandbox that
        was requested, which is by default a local dev server.
        """

        # For introspection URLs with arguments, strip the arguments and any optional
        # slashes, and try url
        # FUTURE - maybe try a lookup of args by name to try URL against fixture
        segments = []
        truncated = False
        for segment in url.split('/'):
            if any( token in segment for token in ( '(', ']' ) ):
                truncated = True
                break
            segments.append( segment )
        url = '/'.join( segments ).strip('[')
        if not url.startswith('/'):
            url = '/' + url
        self.ld("> %s", url)

        # Get a request fixed up with host URL and redirect limit
        try:
            action = 'post' if data else 'get'
            request, response = self._request_and_response( action, url, data=data,
                        redirects=redirects, success_text=success_text, fail=fail )
        except Exception as e:
            if fail:
                self.ls(">>> FAILURE EXPECTED: %s", e)
                return
            elif not truncated:
                raise
            else:
                self.ls("Skipping exception in truncated url: %s", e)
                return

        # Verify MPF view tests are tied to sandbox setup for providers
        if not no_host:
            self.assertTrue( request.sandbox.pk == self.current_sandbox.pk )

        # Checking for success on page if it was rendered
        status_code = response.status_code
        self.l(" %s (%s)", url, status_code)

        if status_code in [ 200 ]:

            # Verify no redirection to login page if login wasn't url target
            # HACK - HARDCODED REFERENCE TO LOGIN URLs
            if url in ['login', 'link'] and not login_redirect:
                template_names = [ t.name for t in response.templates ]
                if 'user/login/frontporch_base.html' in template_names:
                    self.fail("\nBAD LOGIN REDIRECT: %s" % url)

            # Verify no redirections or expected redirection depth
            if redirects:
                previous = response.redirect_chain
                if redirects != len( previous ):
                    self.fail("\nBAD REDIRECT: expected %s, got %s \n%s -> %s\n%s" %
                       (redirects, len(previous), request.mpname, url, previous))
            else:
                # If redirect_chain exists in response, redirect happened previously
                self.assertRaises( AttributeError, lambda: response.redirect_chain )

            # Check for expected text in response
            if success_text is not False:
                content = safe_unicode( response.content )
                text = request.mptest['success_text']
                if content and text and fail ^ ( text in content ):
                    self.ld("SUCCESS FOR URL: %s", url)
                else:
                    self.fail("\nSUCCESS TEXT %s -> %s\nFAIL:   %s\n"
                            "TEST:   %s\nRESULT: \n%s\n......\n%s" % (
                        request.mpname, url, fail, text,
                        content[:256], content[-256:] ))

        # If redirect occurred, if failure wasn't expected try following
        # one more to see if that is successful
        elif status_code in [ 301, 302, 304 ]:
            if fail:
                self.ld("Returning redirect fail: %s -> %s", status_code, url)
                return response
            else:
                self.ld("Handling redirect: %s -> %s", status_code, url)
                return self.get_url( url, must_exist, success_text, fail,
                                      redirects + 1, login_redirect )

        # If url didn't exist, raise error based on whether existence is required
        elif status_code in [ 404, 410 ]:
            if fail:
                self.ld("View 400 passed: %s -> %s", status_code, url)
            elif must_exist:
                self.fail("\nVIEW NOT FOUND: %s" % url)
            else:
                self.ld("No url at: %s", url)

        # Negative testing will generate 400 and 403s
        elif status_code in [ 400, 403, 405 ] and fail:
            self.l("View failed as expected: %s -> %s", status_code, url)

        # Negative testing should not generate 500 responses
        else:
            self.fail("\nBAD RESPONSE CODE: %s -> %s" % (response.status_code, url))

        return response

    def redirect( self, url, **kwargs ):
        self.l("redirect: %s", url)
        _, response = self._request_and_response( 'get', url, redirects=True, **kwargs )
        self._assert_response( url, response, **kwargs )
        return response

    # API methods return values in JSON response
    def fetch_get( self, url, data=None, **kwargs ):
        return self._fetch( 'get', url, data, **kwargs )
    def fetch_post( self, url, data=None, **kwargs ):
        return self._fetch( 'post', url, data, **kwargs )
    def fetch_put( self, url, data='', **kwargs ):
        return self._fetch( 'put', url, data, **kwargs )
    def _fetch( self, method, url, data, **kwargs ):
        try:
            self.l(" fetch_%s: %s  %s", method, url, data)
            _, response = self._request_and_response( method, url, ajax=True, data=data, **kwargs )
            if self._assert_response( url, response, **kwargs ):
                return _load_json_response( response )
        except Exception as e:
            if kwargs.get('fail'):
                self.l(">>> FAILURE EXPECTED: %s", e)
                return
            raise

    def autolookup_get( self, app, model, search, success='text' ):
        """
        HACK - Autolookup endpoint is global, so add helper here
        """
        base = reverse('api_autolookup_model')
        url = f'{base}?search={search}&app={app}&model={model}'
        return self.get_url( url, success_text=success )

    def _assert_response( self, url, response, valid_status=None, redirect=False,
                    fail=False, success_text=None ):
        """
        API calls have different failure modes and responses may be empty or
        asynchronous. Some items like success text are passed on to the code
        itself to check, so shouldn't be checked here.
        """
        if not valid_status:
            if redirect:
                valid_status = [ 200 ] if fail else [ 301, 302 ]
            else:
                valid_status = [ 400, 404, 403, 405, 410 ] if fail else [ 200 ]

        valid = response.status_code in valid_status
        success = getattr( response, 'success', True )

        # First check HTTP response
        # Then check if success flag is present, and if so, true
        if not valid:
            self.fail("\n|  HTTP ERROR: %s -> %s\n|  %s not in %s\n%s" % ( self.current_user,
                        url, response.status_code, valid_status, _content_str(response)))
        if not success:
            self.fail("|  HTTP Response failure reported for: %s\n%s" % (url, response))

        # Return true only if the actual call was supposed to be a success, and was
        return not fail and valid and success

    #--------------------------------------------------------------------
    # App url introspection

    def app_urls_test( self, url_area, urls=None, fail=False, append_slash=False ):
        """
        Requests a view for every screen url prefixed by url_area
        This introspection may look for URLs that don't exist,
        so 404s are not critical errors.
        Not finding any URLs indicates a test config error
        """
        self.l("Getting urls for: %s", url_area)

        if urls is None:
            if not self.mp_urls:
                # Get and cache all default urls if haven't already imported
                self.mp_urls = get_url_list( exclude_prefixes=settings.MP_URL_ADMIN_PAGES )
            urls = self.mp_urls
        self.lv("URLS: %s", urls)

        urls_to_test = self._get_app_urls( urls, area=url_area )
        if not urls_to_test:
            raise Exception("---> NO TEST URLS FOUND FOR:  %s" % url_area)

        for url in urls_to_test:
            if append_slash and not url.endswith('/'):
                url = url + '/'
            self.get_url( url, must_exist=False, fail=fail )

    # Detection of whether url is a regex, which indicates it requires arguments
    _re_no_arg_url = re.compile('[a-z_\-/]')

    def _get_app_urls( self, urls, area=None ):
        """
        Given url pattern list, get list of urls which can be visited directly.
        Intended for introspection of the URL patterns to allow simple URLs without
        parameters to be identified and visited for testing.
        If area is provided, filters urls for that area.
        """
        rv = []
        for url in urls:
            if not area or url.startswith( area ):
                if self._re_no_arg_url.match( url ):
                    rv.append('/' + url)
        return rv

    #--------------------------------------------------------------------
    # Admin url introspection

    def app_root_urls_test( self, app_name, **kwargs ):
        from mpframework.common.admin import root_admin
        return self._test_app_admin_urls( app_name, root_admin,
                    settings.MP_URL_ROOTSTAFF_ADMIN, **kwargs )

    def app_staff_urls_test( self, app_name, **kwargs ):
        from mpframework.common.admin import staff_admin
        return self._test_app_admin_urls( app_name, staff_admin,
                    settings.MP_URL_STAFF_ADMIN, **kwargs )

    def _test_app_admin_urls( self, app_name, admin_site, admin_path,
                    ignore_exceptions=None, fail=False ):
        """
        Requests every registered admin screen for the given app
        and admin site
        """
        self.l("Testing %s views for: %s", admin_site.__class__.__name__, app_name)

        # Look into the admin site to determine if the given
        # model has been registered with the site
        # HACK -- using _registry for this
        models = admin_site._registry

        # Main loop for viewing admin url pages
        from django.contrib.contenttypes.models import ContentType
        for ct in ContentType.objects.filter( app_label=app_name ):
            if ct.model_class() not in models:
                continue
            self.ls("Creating admin URLs for: %s", ct.model)

            # Could get url from the admin site object, but this provides a check
            # from the perspective of typing in expected URL names
            admin_url = '/' + admin_path + '/' + app_name + '/' + ct.model + '/'

            # Test the admin urls for this model
            try:
                # Get the item to test the view
                row_id = self._get_first_valid_row( ct.model_class() )

                # Get the admin object from site registry
                model_admin = models[ ct.model_class() ]

                self._test_admin_urls( admin_url, row_id, model_admin, fail )

            except Exception:
                if ignore_exceptions and any(
                        ignore_str in admin_url for ignore_str in ignore_exceptions ):
                    self.l("Skipping exception for: %s", admin_url)
                else:
                    self.l("Exception for: %s", admin_url)
                    raise

    def _test_admin_urls( self, admin_url, row_id, model_admin, fail ):
        """
        Gets variations on the given admin URL including the list view,
        add, search, and a change view
        ASSUMES ONE DATA ROW EXISTS FOR MODEL
        """

        # If the page exists, test the rest of its URLs
        page = self.get_url( admin_url, must_exist=False, fail=fail )
        if page and page.status_code in [200]:

            # Test editing item
            self.get_url( '{}{}/change/'.format( admin_url, str(row_id) ) )

            # Test search for item
            self.get_url( admin_url + '?q=Search_test_string' )

            # Test add for item
            if getattr( model_admin, 'can_add_item', True ):
                self.get_url( admin_url + 'add/' )

        # The admin page may not be registered, which may not be fatal
        else:
            self.ld("No admin registered for %s", admin_url)


def _load_json_response( response ):

    content = json.loads( response.content )
    if isinstance( content, dict ):
        if content.get('values'):
            return content['values']
        return content
    return _content_str( response )

def _content_str( response ):
    content = getattr( response, 'content', None )
    rv = ( "Streaming content..." if not content else
                "%s\n.......\n%s" % (
                safe_unicode(content)[:256], safe_unicode(content)[-256:]) )
    return rv
