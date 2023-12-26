#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Selenium select2 support

"""

# Selenium is not loaded on production servers
try:
    from selenium.webdriver import ActionChains
except Exception:
    pass


class SelenSelect2:

    def __init__( self, stc, hidden, s2 ):
        self.stc = stc
        self.hidden = hidden
        self.s2 = s2

    def get_by_visible_text( self, text ):
        for item in self.items:
            if text in item.text:
                return item

    def select_by_visible_text( self, text ):
        self.click( self.get_by_visible_text( text ) )

    def click( self, element=None ):
        if element is None:
            element = self.s2
        ActionChains( self.stc.sln )\
            .click_and_hold( element )\
            .release( element )\
            .perform()

    def open( self ):
        if not self.is_open:
            self.click()

    def close( self ):
        if self.is_open:
            self.click()

    @property
    def is_open( self ):
        return 'select2-container--open' in self.s2.get_attribute('class')

    @property
    def dropdown( self ):
        return self.stc.get_css('.select2-dropdown')

    @property
    def items( self ):
        self.open()
        return self.dropdown.find_elements_by_css_selector('.select2-results li > span')
