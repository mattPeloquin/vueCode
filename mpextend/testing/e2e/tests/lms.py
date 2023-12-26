#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for content models and related application tests
"""

import os
from django.conf import settings

from mpframework.testing.e2e.tests.base import SystemTestCase


@SystemTestCase.register
class LmsTests( SystemTestCase ):

    def test_add_lesson_and_play(self):
        self.login()
        # Go to lms and bring up new lms form
        self.go_url("/content/lmsitems")
        self.get_xpath('//input[@value="Add New LmsItem"]').click()
        # Fill out the form and submit
        self.get_name("lesson_name").send_keys("Test1")
        self.get_name("lesson_package_file").send_keys(os.path.join(settings.MP_TEST_FOLDERS_PACKAGES[0], 'LMSTEST_Battle.zip'))
        self.get_xpath('//input[@value="Upload and add LMS package"]').click()
        # Go to the student portal and play lesson from all tab
        self.go_home()
        self.go_hash("learn")
        self.go_hash("learn_all")
        self._play_lesson("div_lesson_all_0", "Test1")
        self.logout()

    def test_add_course_and_play_lesson(self):
        self.login()
        # Add course with BP lesson to our plan
        self.go_hash("plan")
        self.go_hash("plan_create")
        self.drag_drop(
                self.get_xpath("//div[text()='TestCourse1']"),
                self.sln.find_element_by_xpath("id('div_roots_plan_0')"))
        # The BP lesson should be in remaining plan items
        self.go_hash("learn")
        self.go_hash("learn_lessons")
        self._play_lesson("div_lesson_remaining_0", "BattleProof")
        self.logout()


    def _play_lesson(self, collection, lesson):
        """
        Use name of collection and lesson to do double click on a lesson, since in a
        environment the package will need to be mounted
        """
        lesson_xpath = "id('" + collection + "')/descendant::div[text()[contains(.,'" + lesson + "')]]"
        # Click lesson
        self.screenshot()
        self.get_xpath(lesson_xpath).click()
        # If lesson is not already mounted, have to dismiss dialog, wait a bit, and click again
        not_ready_dialog = self.get_xpath(
                "//div[@id='msg_info']/../descendant::span[@class='fa fa-angle-down']",
                wait=2 )
        if not_ready_dialog:
            self.screenshot()
            not_ready_dialog.click()
            self.get_xpath( lesson_xpath, screenshot=True ).click()

        # Take a picture of lesson and leave
        self.get_id( "header", screenshot=True ).click()

