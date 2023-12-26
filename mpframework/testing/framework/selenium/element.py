#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF wrapping of Selenium WebElement to add additional
    robustness in dealing with responsive UI

    CAN ONLY BE IMPORTED WHEN SELENIUM IS PRESENT
"""
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException

from mpframework.common import log
from mpframework.common.utils import join_paths

from .. import mpTestingException


class mpWebElement( WebElement ):
    """
    Override and extend Selenium WebElement to handle some common issues
    """

    @classmethod
    def find( cls, stc, find_fn, find_arg, **kwargs ):
        """
        Convenience factory for calling Selenium find methods and returning
        first or list of mpWebElements based on whether currently displayed.
        """
        first = kwargs.pop( 'first', True )
        display = kwargs.pop( 'display', False )
        rv = False if first else []
        elements = find_fn( find_arg, **kwargs )
        for element in elements:
            if not display or element.is_displayed():
                mp_element = cls( stc, element )
                if first:
                    rv = mp_element
                    break
                else:
                    rv.append( mp_element )
        return rv

    def __init__( self, stc, selenium_webelement ):

        # Store test case for access to utilities, primarily logging
        self.stc = stc

        # Clone the selenium web element state
        self._parent = selenium_webelement.parent
        self._id = selenium_webelement.id
        self._w3c = selenium_webelement._w3c

    def __str__( self ):
        return "WebElement: {}({})='{}'".format( self.tag_name, str(self.location),
                                                  self.text[:32] )

    def get_css( self, selector, **kwargs ):
        """
        Return mpWebElement for CSS search underneath us
        """
        return self.find( self.stc, self.find_elements_by_css_selector,
                            selector, **kwargs )

    def ensure_visible( self, **kwargs ):
        """
        Do more than Selenium default to bring an element into view so
        it can be manipulated
        """
        required = kwargs.get( 'required', False )
        try:
            if not self.is_displayed():
                ActionChains( self.parent ).move_to_element( self ).perform()

            rv = self.is_displayed()
            if not required or rv:
                return rv

            raise mpTestingException("ELEMENT NOT VISIBLE: %s", str(self))

        except WebDriverException as e:
            log.info("Exception in ensure_visible: %s -> %s", self, e)

    def click( self, **kwargs ):
        """
        Work around issues clicking elements in responsive layouts where
        items may not be visible or are overlaid
        """
        try:
            if self.ensure_visible( **kwargs ):
                self.stc.l("Clicking: %s", str(self))
                return super().click()

        # Try Click with javascript if click failed
        except WebDriverException:
            self.stc.l("Using JS click: %s", str(self))
            self.parent.execute_script('arguments[0].click();', self)

    def send_keys( self, value, *args, **kwargs ):
        """
        Make sure element is visible before trying to send keys, and
        make any adjustments according to type
        """
        replace = kwargs.pop( 'replace', True )
        if self.ensure_visible( **kwargs ):
            self.stc.l("Sending keys: %s -> %s, %s", str(self), value, args )
            if replace:
                self.clear()

            # Append fixture path for file uploads
            if self.get_attribute('type') == 'file':
                value = join_paths( self.stc.testing_path, 'fixtures', 'uploads', value )

            return super().send_keys( value, *args, **kwargs )

    @property
    def value( self ):
        """
        Returns the "value" of the element, which will vary depending on its type
        """
        rv = None

        if self.get_attribute('type') == 'file':
            # For file rely on file control's use of file name
            rv = self.find_element_by_xpath(
                            './/../../*[contains(@class,"mp_file_name")]'
                            ).text

        elif self.get_attribute('type'):
            rv = self.get_attribute('value')

        else:
            rv = self.text

        return rv

