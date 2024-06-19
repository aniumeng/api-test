#!/usr/bin/env python
# -*- coding: utf-8 -*-


from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, \
    UnexpectedTagNameException
from selenium.common.exceptions import StaleElementReferenceException
import time


class Select(object):

    def __init__(self, webelement):
        """
        Constructor. A check is made that the given element is, indeed, a
        SELECT tag. If it is not,
        then an UnexpectedTagNameException is thrown.

        :Args:
         - webelement - element SELECT element to wrap

        Example:
            from selenium.webdriver.support.ui import Select \n
            Select(driver.find_element_by_tag_name("select")).select_by_index(2)
        """
        if webelement.tag_name.lower() != "input" and \
                "el-select" not in webelement.get_attribute("class"):
            raise UnexpectedTagNameException(
                "Select only works on <el-select> elements, not on <%s>" %
                webelement.tag_name)
        self._el = webelement
        self._dropdown = self._el. \
            find_element(By.XPATH,
                         "./ancestor::div/following-sibling::div"
                         "[starts-with(@class, 'el-select-dropdown el-popper')]")
        multi = self._el.get_attribute("multiple")
        self.is_multiple = multi and multi != "false"

    def set_multiple(self):
        self.is_multiple = True

    @property
    def options(self):
        """Returns a list of all options belonging to this select tag"""
        # return self._el.find_elements(By.TAG_NAME, 'li')
        return self._dropdown.find_elements(By.XPATH, './/ul//li')

    @property
    def tag_options(self):
        """Returns a list of all server_tag options belonging to
        this select tag"""
        return self._el.find_elements(By.XPATH, './/ul//li')

    @property
    def all_selected_options(self):
        """Returns a list of all selected options belonging to this select tag"""
        # ret = []
        # for opt in self.options:
        #     if self._is_selected(opt):
        #         ret.append(opt)
        # return ret
        options = self._el.find_elements(
            By.XPATH, './/div[contains(@class, "salus-select-selection")]//li')
        return options

    @property
    def first_selected_option(self):
        """The first selected option in this select tag (or the currently selected option in a
        normal select)"""
        for opt in self.options:
            if self._is_selected(opt):
                return opt
        raise NoSuchElementException("No options are selected")

    def add_a_value(self, value):
        """Select add a options

        :param value: The value to add
        :return:
        """
        self._el.click()
        self._el.find_element(By.CSS_SELECTOR, 'input').send_keys(value)
        if self.tag_options[0].get_attribute('title') == value and 'selected' \
                in self.tag_options[0].get_attribute('class'):
            self.select_by_value(value)
        else:
            css = ".//li[@title =%s]//i" % self._escapeString(value)
            self._el.find_element(By.XPATH, css).click()
        self._is_open() and self._el.click()

    def select_by_value(self, value):
        """Select all options that have a value matching the argument. That is, when given "foo" this
           would select an option like:

           <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

           throws NoSuchElementException If there is no option with specisied value in SELECT
           """
        self._drop_layer(close=False)
        css = "li[title =%s]" % self._escapeString(value)
        opts = self._dropdown.find_elements(By.CSS_SELECTOR, css)
        matched = False
        for opt in opts:
            self._setSelected(opt)
            if not self.is_multiple:
                self._is_open() and self._el.click()
                return
            matched = True
        if not matched:
            raise NoSuchElementException("Cannot locate option with value: %s" % value)
        self._drop_layer(close=True)

    def select_by_values(self, values):
        """Select all options that have a value matching the argument. That is, when given "foo" this
           would select an option like:

           <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

           throws NoSuchElementException If there is no option with specisied value in SELECT
           """
        self._drop_layer(close=False)
        css_list = ["li[title=%s]" % self._escapeString(value) for value in values]
        for css in css_list:
            opts = self._dropdown.find_elements(By.CSS_SELECTOR, css)
            matched = False
            for opt in opts:
                self._setSelected(opt)
                matched = True
                break
            if not matched:
                raise NoSuchElementException("Cannot locate option with value: %s" % values)
        self._drop_layer(close=True)

    def select_by_index(self, index):
        """Select the option at the given index. This is done by examing the "index" attribute of an
           element, and not merely by counting.

           :Args:
            - index - The option at this index will be selected

           throws NoSuchElementException If there is no option with specisied index in SELECT
           """
        self._drop_layer(close=False)
        match = int(index)
        try:
            opt = self.options[match]
        except ValueError as e:
            raise NoSuchElementException(
                "Could not locate element with index %d" % index)
        self._setSelected(opt)
        self._drop_layer(close=True)

    def select_by_visible_text(self, text):
        """Select all options that display text matching the argument. That is, when given "Bar" this
           would select an option like:

            <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against

            throws NoSuchElementException If there is no option with specisied text in SELECT
           """
        self._drop_layer(close=False)
        xpath = ".//ul/li[normalize-space(.) = %s]" % self._escapeString(text)
        opts = self._dropdown.find_elements(By.XPATH, xpath)
        matched = False
        for opt in opts:
            self._setSelected(opt)
            if not self.is_multiple:
                self._is_open() and self._el.click()
                return
            matched = True

        if len(opts) == 0 and " " in text:
            subStringWithoutSpace = self._get_longest_token(text)
            if subStringWithoutSpace == "":
                candidates = self.options
            else:
                xpath = ".//li[contains(.,%s)]" % self._escapeString(subStringWithoutSpace)
                candidates = self._el.find_elements(By.XPATH, xpath)
            for candidate in candidates:
                if text == candidate.text:
                    self._setSelected(candidate)
                    self._is_open() and self._el.click()
                    if not self.is_multiple:
                        return
                    matched = True

        if not matched:
            raise NoSuchElementException("Could not locate element with visible text: %s" % text)
        self._drop_layer(close=True)

    def select_by_partial_text(self, text):
        """Select all options that display text matching the argument. That is, when given "Bar" this
           would select an option like:

            <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against

            throws NoSuchElementException If there is no option with specisied text in SELECT
           """
        self._drop_layer(close=False)
        xpath = ".//li[contains(.,%s)]" % self._escapeString(text)
        opts = self._dropdown.find_elements(By.XPATH, xpath)
        matched = False
        for opt in opts:
            self._setSelected(opt)
            if not self.is_multiple:
                self._is_open() and self._el.click()
                return
            matched = True

        if not matched:
            raise NoSuchElementException("Could not locate element with visible text: %s" % text)
        self._drop_layer(close=True)

    def select_by_partial_texts(self, texts):
        """Select all options that display text have the argument. That is, when given "Bar" this
           would select an option like:

            <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against

            throws NoSuchElementException If there is no option with specisied text in SELECT
           """
        self._drop_layer(close=False)
        xpath_s = [".//span[contains(.,%s)]" % self._escapeString(text) for text in texts]
        for xpath in xpath_s:
            opts = self._dropdown.find_elements(By.XPATH, xpath)
            matched = False
            for opt in opts:
                self._setSelected(opt)
                matched = True
                break

            if not matched:
                raise NoSuchElementException("Could not locate element with visible text: %s" % texts)
        self._drop_layer(close=True)

    def deselect_all(self):
        """Clear all selected entries. This is only valid when the SELECT supports multiple selections.
           throws NotImplementedError If the SELECT does not support multiple selections
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect all options of a multi-select")
        # for opt in self.all_selected_options:
        #     self._unsetSelected(opt)
        for opt in self.all_selected_options:
            cross = opt.find_element(By.XPATH, './/i[@class="salus-icon-pop-close-o"]')
            cross.click()

    def deselect_by_value(self, value):
        """Deselect all options that have a value matching the argument. That is, when given "foo" this
           would deselect an option like:

            <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

            throws NoSuchElementException If there is no option with specisied value in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        matched = False
        # css = "option[value = %s]" % self._escapeString(value)
        # opts = self._el.find_elements(By.CSS_SELECTOR, css)
        opts = self.all_selected_options
        for opt in opts:
            val = opt.get_attribute('title')
            if value == val:
                self._unsetSelected(opt)
                matched = True
        if not matched:
            raise NoSuchElementException("Could not locate element with value: %s" % value)

    def deselect_by_values(self, values):
        """Deselect all options that have a value matching the argument. That is, when given "foo" this
           would deselect an option like:

            <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

            throws NoSuchElementException If there is no option with specisied value in SELECT
        """
        for value in values:
            matched = False
            opts = self.all_selected_options
            for opt in opts:
                val = opt.get_attribute('title')
                if value == val:
                    self._unsetSelected(opt)
                    matched = True
                    break
            if not matched:
                raise NoSuchElementException("Could not locate element with value: %s" % value)

    def deselect_by_index(self, index):
        """Deselect the option at the given index. This is done by examing the "index" attribute of an
           element, and not merely by counting.

           :Args:
            - index - The option at this index will be deselected

            throws NoSuchElementException If there is no option with specisied index in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        for opt in self.all_selected_options:
            if opt.get_attribute("index") == str(index):
                self._unsetSelected(opt)
                return
        raise NoSuchElementException("Could not locate element with index %d" % index)

    def deselect_by_visible_text(self, text):
        """Deselect all options that display text matching the argument. That is, when given "Bar" this
           would deselect an option like:

           <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        matched = False
        # xpath = ".//option[normalize-space(.) = %s]" % self._escapeString(text)
        # opts = self._el.find_elements(By.XPATH, xpath)
        opts = self.all_selected_options
        for opt in opts:
            txt = opt.text
            if txt == text:
                self._unsetSelected(opt)
                matched = True
        if not matched:
            raise NoSuchElementException("Could not locate element with visible text: %s" % text)

    def deselect_by_partial_text(self, text):
        """Deselect all options that display text matching the argument. That is, when given "Bar" this
           would deselect an option like:

           <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        matched = False
        # xpath = ".//option[normalize-space(.) = %s]" % self._escapeString(text)
        # opts = self._el.find_elements(By.XPATH, xpath)
        opts = self.all_selected_options
        for opt in opts:
            txt = opt.text
            if text in txt:
                self._unsetSelected(opt)
                matched = True
        if not matched:
            raise NoSuchElementException("Could not locate element with visible text: %s" % text)

    def _setSelected(self, option):
        if not self._is_selected(option):
            time.sleep(0.8)
            _ = option.location_once_scrolled_into_view
            option.click()
        else:
            self._el.click()

    def _unsetSelected(self, option):
        if self._is_selected(option):
            time.sleep(0.1)
            _ = option.location_once_scrolled_into_view
            option.click()
        else:
            crosses = option.find_elements(By.XPATH, './/i[@class="salus-icon-pop-close-o"]')
            if any(crosses):
                cross = crosses[0]
                cross.click()
            else:
                raise NoSuchElementException("Cloud not locate x button for element with option: %s" % option)

    def _escapeString(self, value):
        if '"' in value and "'" in value:
            substrings = value.split("\"")
            result = ["concat("]
            for substring in substrings:
                result.append("\"%s\"" % substring)
                result.append(", '\"', ")
            result = result[0:-1]
            if value.endswith('"'):
                result.append(", '\"'")
            return "".join(result) + ")"

        if '"' in value:
            return "'%s'" % value

        return "\"%s\"" % value

    def _get_longest_token(self, value):
        items = value.split(" ")
        longest = ""
        for item in items:
            if len(item) > len(longest):
                longest = item
        return longest

    def _is_selected(self, option):
        class_text = option.get_attribute("class")
        selected = "el-select-dropdown__item selected" in class_text
        return selected

    def _drop_layer(self, close=True):
        closed = not self._is_open()
        if close != closed:
            if self.is_multiple:
                path = './/span[contains(@class, "salus-select-arrow")]'
                arrow = self._el.find_element(By.XPATH, path)
                arrow.click()
            else:
                self._el.click()

    def _is_open(self):
        time.sleep(0.5)
        try:
            class_text = self._el.get_attribute("readonly") or "Failed"
            _open = False or "readonly" in class_text
            return _open
        except StaleElementReferenceException:
            return False
        # _open = "salus-select-open" in class_text

    def _get_longest_token(self, value):
        items = value.split(" ")
        longest = ""
        for item in items:
            if len(item) > len(longest):
                longest = item
        return longest