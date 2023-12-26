#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Selenium test case support

    Selenium test cases support the following:

     - Running independent unit tests for apps
     - Running system tests

    Tests start with the normal fixture tests data.
    Unit tests may add some data, but each one's data independent.
    System tests will have data workflow dependencies, with the
    data being built up in the tests (vs. here using fixture
    loading or shared code).

    Tests may be run against local or remote targets, using
    either Firefox selenium or Chrome/IE servers

    FUTURE -- Grid support
    FUTURE -- Tests may be run on an external hosted service, so
    keep dependencies on running tests in this framework to minimum
"""
import time
import random
from django.conf import settings

# Selenium is not loaded on production servers
try:
    from selenium import webdriver
    from selenium.webdriver import ActionChains
    from selenium.webdriver.support.select import Select
    from selenium.common.exceptions import WebDriverException
    from selenium.common.exceptions import StaleElementReferenceException
    from .wait import wait_web_element
except Exception:
    pass

# Windows support to detect keyboard hit in console for moving waits too long
try:
    import msvcrt
    kbhit = msvcrt.kbhit
except:
    kbhit = lambda: False

from mpframework.common import log
from mpframework.common.utils import join_paths
from mpframework.common.utils.file import create_local_folder
from mpframework.common.deploy.paths import mpframework_path
from mpframework.common.deploy.paths import work_path

from .js_error import stop_js_error
from .select import SelenSelect2


WAIT_IMPLICIT = 0.1


class SeleniumTestCaseMixin:
    """
    Mixin class for Selenium UI tests

    Elements must be visible to be interacted with through Selenium,
    so test scripts need to click menu items based on visibility to logged-in user
    """

    drivers = {
        'chrome': ( 'Chrome', '.tools/chromedriver.exe' ),
        'edge': ( 'Edge', '.tools/MicrosoftWebDriver.exe' ),
        'firefox': ( 'Firefox', '.tools/geckodriver.exe' ),
        'safari': ( 'Safari', '/usr/bin/safaridriver' ),
        }

    close_browser_on_exit = False

    """-------------------------------------------------------------------
        Core selectors that return a Selenium WebElement

        Each of these returns the FIRST visible match; be careful that
        more than one visible element is matching.

        See Wait Visible discussion below for how waiting until elements
        are visible to Selenium is managed
    """

    @stop_js_error
    def get_id( self, id, **kwargs ):
        if kwargs.pop( 'show_hidden', False ):
            self.sln.execute_script( '$("#{}").show()'.format( id ) )
            self.sln.execute_script( '$("#{}").each( function() {{'
                 'if( this.type == "hidden" ) this.type="text"; }} )'.format( id ) )
        return self.wait_visible( self.sln.find_elements_by_id, id, **kwargs )

    def get_list_from_id( self, id, **kwargs):
        html_list = self.get_id(id)
        return html_list.find_elements_by_tag_name("li")

    @stop_js_error
    def get_name( self, name, **kwargs ):
        return self.wait_visible( self.sln.find_elements_by_name, name, **kwargs )

    @stop_js_error
    def get_css( self, selector, **kwargs ):
        return self.wait_visible( self.sln.find_elements_by_css_selector,
                                  selector, **kwargs )
    @stop_js_error
    def get_xpath( self, search, **kwargs ):
        return self.wait_visible( self.sln.find_elements_by_xpath, search, **kwargs )

    def get_class_text( self, css, text, xpath=None ):
        """
        Get first item by class name and text, with optional xpath add-on search
        """
        search = '//*[ contains(@class, "{}")]//*[ text()[contains(., "{}")] ]'
        search = search.format( css, text )
        if xpath:
            search = search + '{}'.format( xpath )
        return self.get_xpath( search )


    """-------------------------------------------------------------------
        Convenience actions
    """

    def upload_file( self, id, name, **kwargs ):
        """
        Send name to file input with the given ID
        Supports upload with a normal file input field that will POST file and
        s3direct upload controls, which will load via JS via different fields.
        This has to check for one case before trying the other, so it doesn't
        wait for the normal input to be available.
        """
        rv = self.get_id( id, wait=0, required=False )
        if rv:
            rv.send_keys( name )
        else:
            rv = self.get_css( '.{} .mp_file_input'.format( id ), **kwargs )
            rv.send_keys( name )

            # Try each second for a limited amount until name field visible,
            # which signals the upload is complete
            _IMAGE_TRIES = 4
            wait = 1
            while( wait ):
                name = self.get_css( '.{} .mp_file_name'.format( id ),
                                     wait=wait, required=False, log=False )
                if not name and wait < _IMAGE_TRIES:
                    wait += 1
                else:
                    wait = False
        return rv

    def click_css( self, css, **kwargs ):
        """
        Clicks the element IF IT IS VISIBLE, nothing otherwise
        """
        element = self.get_css( css, required=False, **kwargs )
        if element:
            element.click()
        else:
            self.l("SKIPPING click_css: %s" % css)

    def click_dropdown( self, css, text ):
        """
        Selects the visible text of either Select or Select2 dropdown
        """
        self.get_select( css ).select_by_visible_text( text )

    def escape( self ):
        self.l("Clicking escape key")
        ActionChains( self.sln )\
            .send_keys( webdriver.common.keys.Keys.ESCAPE )\
            .perform()

    @stop_js_error
    def go_anchor( self, anchor ):
        self.l("GO ANCHOR: #%s", anchor)
        search = '//a[ contains( text(), "{}" ) ]'.format( anchor )
        self.get_xpath( search, screenshot=True ).click()
        self.wait_point()

    @stop_js_error
    def go_hash( self, anchor ):
        self.l("GO HASH: #%s", anchor)
        search = '//a[ @href="#{}" ]'.format( anchor )
        self.get_xpath( search, screenshot=True ).click()
        self.wait_point()

    """--------------------------------------------------------------------
        Other handy utilities are in the section below
        Also remember the Selenium commands:
            self.sln.back()
            self.sln.forward()
    """

    @stop_js_error
    def go_url( self, url, success='', fail='404', full=False, refresh=False ):
        """
        Navigate to given url if not already there
        """
        if not refresh and self.sln.current_url.endswith( url ):
            return
        if not full:
            url = '{}{}'.format( self.site_url, url )
        self.l("Navigating to: %s", url)
        self.sln.get( url )
        self.screenshot()
        if success:
            rv = success in self.sln.page_source.lower()
        else:
            rv = fail not in self.sln.page_source.lower()
        return rv

    @stop_js_error
    def drag_drop( self, source, target ):
        self.l("Dragging %s to %s", source, target)
        ActionChains( self.sln )\
            .drag_and_drop( source, target )\
            .perform()
        self.wait_not_visible( self.sln.find_element_by_css_selector, '.mp_spinner' )

    def screenshot( self ):
        if self.screenshots:
            try:
                name = "{}_{}.png".format( self._testMethodName, self._screenshot_number )
                path = join_paths( self._screenshot_folder, name )
                self.sln.get_screenshot_as_file( path )
                self._screenshot_number += 1
            except Exception as e:
                self.l("Failure to take screenshot: %s", e)

    def get_select( self, css, **kwargs ):
        """
        Returns Select object for working with select boxes
        """
        element = self.get_css( css )
        s2 = self.get_css( '{} + .select2'.format( css ), required=False, wait=0.2 )
        if s2:
            rv = SelenSelect2( self, element, s2 )
        else:
            rv = Select( element )
        self.ld("Got select element: %s -> %s", css, rv)
        return rv

    def wait_point( self, seconds=None ):
        """
        Wait explicitly or based on wait option, and grab snapshot
        On windows, exit wait when key is hit in terminal to support debugging
        """
        if not seconds:
            seconds = self.wait
        seconds = float( seconds )
        if seconds > 0.01:
            self.l("Waiting %s", seconds)
            increment = 0.2
            wait = 0.0
            while( wait < seconds ):
                if kbhit():
                    self.l("Breaking wait")
                    break
                time.sleep( increment )
                wait += increment
        self.screenshot()


    def set_window_small( self, random=True ):
        if random:
            self.set_window_random( 300, 400, 300, 600 )
        else:
            self.set_window_size( 300, 400 )

    def set_window_norm( self, random=True ):
        if random:
            self.set_window_random( 600, 1200, 800, 1600 )
        else:
            self.set_window_size( 800, 1200 )

    def set_window_random( self, wmin=300, wmax=1800, hmin=300, hmax=1800 ):
        self.set_window_size( random.randrange( wmin, wmax ),
                              random.randrange( hmin, hmax ) )

    def set_window_size( self, width, height ):
        # Wrap selenium set_window_size because it sometimes throws exceptions
        try:
            self.sln.set_window_size( width, height )
            self.wait_point()
        except Exception as e:
            self.l("Exception setting window size: %s", e)

    def set_window_max( self ):
        try:
            self.sln.maximize_window()
            self.wait_point()
        except Exception as e:
            self.l("Exception maximizing window size: %s", e)


    #--------------------------------------------------------------------
    # Test case setup

    @classmethod
    def setUpClass( cls ):
        super().setUpClass()

        cls.browser = settings.MP_TEST_BROWSER
        cls.testing_path = mpframework_path( 'testing' )

        name, file = cls.drivers[ cls.browser ]
        driver_file = join_paths( cls.testing_path, '../..', file )
        log.debug("Loading: %s", driver_file)

        driver = getattr( webdriver, name )
        cls.sln = driver( executable_path=driver_file )
        cls.sln.implicitly_wait( WAIT_IMPLICIT )
        log.info("Started %s: %s", cls.browser, cls.sln)

    @classmethod
    def tearDownClass( cls ):
        if cls.close_browser_on_exit:
            cls.sln.quit()
        super().tearDownClass()

    def __init__( self, *args, **kwargs ):
        super().__init__( *args )

        # Add pauses into test execution
        self.wait = float( kwargs.pop( 'wait', settings.MP_TEST_WAIT ) )

        # Capture screen shows by default in work folder for test type
        self.screenshots = kwargs.pop( 'screenshots', True )
        if self.screenshots:
            self._screenshot_folder = work_path('.screen_shots', self.__class__.__name__)
            create_local_folder( self._screenshot_folder )
            self._screenshot_number = 1


    """--------------------------------------------------------------------
        Custom wait until visible support
        Default is to return ONLY FIRST item that matches

        MPF's UI is dynamic and a single page app in many areas,
        so to make UI tests less brittle, all Selenium access is wrapped
        in custom wait logic allows time for items to become visible.
    """

    def wait_visible( self, find_fn, find_arg, **kwargs ):
        """
        Wait until the element defined by find_fn is visible
        """
        kwargs.pop('log',True) and self.l("Finding: %s", find_arg )
        rv = wait_web_element( self, find_fn, find_arg, **kwargs )
        if rv:
            self.ld("Wait visible found: %s -> %s", find_arg, str(rv) )
        return rv

    def wait_not_visible( self, find_fn, find_arg, **kwargs ):
        """
        Wait until the element is NOT visible
        """
        rv = wait_web_element( self, find_fn, find_arg, visible=False, **kwargs )
        self.l("Wait NOT visible: %s" % rv)
        return rv
