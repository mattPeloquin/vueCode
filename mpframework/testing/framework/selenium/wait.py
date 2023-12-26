#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF additions to Selenium waiting for extra robustness of tests

    CAN ONLY BE IMPORTED WHEN SELENIUM IS PRESENT
"""

import time

from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException

from .. import mpTestingException
from .element import mpWebElement

# Waiting for web elements is separate from other waiting
WAIT_TIMEOUT = 0.6
WAIT_POLL = 0.1


def wait_web_element( stc, find_fn, find_arg, **kwargs ):
    """
    Wait for and wrap web element into a MPF web element.
    Default is to return the first displayed element, but options
    to return list of displayed, and all that are visible
    """
    required = kwargs.pop( 'required', True )
    visible = kwargs.pop( 'visible', True )

    wait = Wait( stc, kwargs )

    def element_wait_test():
        return mpWebElement.find( stc, find_fn, find_arg, **kwargs )

    rv = wait.until( element_wait_test, visible, find_arg )
    if not required or bool(rv) == visible:
        return rv
    else:
        raise mpTestingException("FAILED ELEMENT WAIT: %s -> %s" %
                ( find_arg, kwargs ))


class Wait( WebDriverWait ):
    """
    Wrap WebDriverWait and the driver implicit wait to handle wider variety of exceptions
    and add some additional functionality including incrementally increasing poll.
    """

    def __init__( self, stc, kwargs ):
        """
        Allow wait for visible to be overridden by testing wait setting
        """
        poll = float( kwargs.pop( 'poll', WAIT_POLL ) )
        timeout = float( kwargs.pop( 'wait', stc.wait if stc.wait > 0.01 else WAIT_TIMEOUT ) )
        super().__init__( stc.sln, timeout, poll )
        self.stc = stc
        self.screenshot_when_done = kwargs.pop( 'screenshot', False )

    def until( self, method, loop_until_positive, message ):
        """
        Calls the method provided until the bool return value of method
        matches loop_until_positive.
        """
        poll = 0
        end_time = time.time() + self._timeout
        while( True ):
            try:
                rv = method()

                if bool( rv ) == bool( loop_until_positive ):
                    if self.screenshot_when_done:
                        self.stc.screenshot()
                    return rv

            except NoSuchElementException:
                if not loop_until_positive:
                    self.stc.ld("Exiting wait for NoSuchElementException: %s", message)
                    raise

            # Items that can normally be ignored
            except ( StaleElementReferenceException,
                     WebDriverException ) as e:
                self.stc.ld("WEBDRIVER wait exception: %s", e)

            if( time.time() > end_time ):
                break

            self.stc.l("WEBDRIVER WAIT: %s", message)
            time.sleep( poll )
            poll += self._poll
        return False
