#!/usr/bin/env python
# -*- coding: utf-8 -*-


import linecache
import logging
import os
import time
import sys

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
# from selenium.webdriver.support.select import Select
from common.el_select import Select
from selenium.webdriver.support.wait import WebDriverWait

from common.utility import CloudConf
from common.utility import WebDriverManager

log = logging.getLogger(__name__)


class Condition(object):
    """等待元素状态"""
    # ----------element：单个元素--------------------------
    present = ec.presence_of_element_located
    # 等待元素出现在DOM，但不保证可见
    visible = ec.visibility_of_element_located
    # 等待元素出现在DOM，同时可见(宽高不为0)
    click_enable = ec.element_to_be_clickable
    # 等待元素出现在DOM，同时可见，可以点击

    # ----------elements：多个元素--------------------------
    presents_all = ec.presence_of_element_located
    # 等待多元素 所有 出现在DOM，但不保证可见
    visible_all = ec.visibility_of_all_elements_located
    # 等待多元素 所有 出现在DOM，同时可见(宽高不为0)
    visible_any = ec.visibility_of_any_elements_located
    # 等待多元素 任一 出现在DOM，同时可见(宽高不为0)


class element_by_parent(object):
    def __init__(self, locator, parent):
        self.locator = locator
        self.parent = parent

    def __call__(self, driver):
        if self.parent is None:
            element = driver.find_element(*self.locator)
            return element
        else:
            element = self.parent.find_element(*self.locator)
            return element


class ActionBase(object):
    def __init__(self):
        self.web_driver = WebDriverManager().web_driver
        self.config = CloudConf()

    def get_screen_shot(self, element, **kwargs):
        """get screen shot and register to web_driver

        :param element: web element object
        :param kwargs:
        :return:
        """

        screen_shot = self.web_driver.get_screenshot_as_png()
        element_rect = dict()
        element_rect.update(element.location)
        element_rect.update(element.size)
        func_name = sys._getframe(1).f_code.co_name
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        glance = dict(
            screen_shot=screen_shot, element_rect=element_rect,
            element=element, func_name=func_name,
            timestamp=timestamp
        )
        f = sys._getframe(3)
        if f:
            co, lineno = f.f_code, f.f_lineno
            filename, name = co.co_filename, co.co_name
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            line = line.strip() if line else None
            _, filename = os.path.split(filename)
            util_info = "File '%s', method %s, line %s, %s" % \
                        (filename, name, lineno, line)
            glance.update(dict(util_info=util_info))
        glance.update(kwargs)
        if len(self.web_driver.screen_shots) >= 3:
            head1 = self.web_driver.screen_shots.pop(0)
            del head1
        self.web_driver.screen_shots.append(glance)

    def max_window(self):
        """:return: 最大化窗口"""
        self.web_driver.maximize_window()

    def get(self, value):
        """:param value: 转向地址"""
        self.web_driver.get(value)

    def wait(self, seconds):
        """:param seconds:    等待时间"""
        self.web_driver.implicitly_wait(seconds)

    def close(self):
        """关闭窗口"""
        self.web_driver.close()

    def quit(self):
        """退出浏览器"""
        self.web_driver.quit()

    def back(self):
        """功能：返回"""
        self.web_driver.back()

    def forward(self):
        self.web_driver.forward()

    def f5(self):
        """功能：刷新页面"""
        self.web_driver.refresh()

    def get_title(self):
        """功能:得到浏览器的标题"""
        return self.web_driver.title

    def get_url(self):
        """功能:得到浏览器的url"""
        return self.web_driver.current_url

    def get_shot(self, value):
        """功能：截图并保存
        :param value:  文件路径
        """
        self.web_driver.get_screenshot_as_file(value)

    def execute_js(self, value):
        """执行JS

        :param value:  js查找元素方式，或jQuery
        :return:    找到元素
        """
        return self.web_driver.execute_script(value)

    def input_by_id_js(self, id_element, value):
        """根据id输入文本

        :param value:  文本值
        :param id_element: 框的id
        :return:
        """

        js = "document.getElementById('" + id_element\
             + "').value='" + value + "'"
        self.execute_js(js)
        self.web_driver.find_element_by_id(id_element).send_keys(" ")

    def scroll_to_element(self, value):
        """滑动到元素

        :param value:  文本值
        :return:
        """

        element = self.execute_js(value)
        self.web_driver.execute_script(
            "arguments[0].scrollIntoViewIfNeeded(true);", element)

    def scoll_to_top(self):
        """功能：滚动到浏览器最顶部"""
        self.web_driver.execute_script("window.scrollTo(0,0);")

    def find_element(self, locator, parent=None):
        """Find element by locator, from html body or parent element.

        :param locator:  定位方式(by, value)
        :param parent:   父元素
               默认--从HTML根节点开始查找，全局查找
               指定--从元素的子类开始查找，作用域内查找
        """

        by, value = locator
        father = parent or self.web_driver
        gps = {
            "id": father.find_element_by_id,
            "name": father.find_element_by_name,
            "class": father.find_element_by_class_name,
            "text": father.find_element_by_link_text,
            "text_part": father.find_element_by_partial_link_text,
            "xpath": father.find_element_by_xpath,
            "css": father.find_element_by_css_selector,
            "tag": father.find_element_by_tag_name
        }
        func = gps.get(by)
        if func:
            ele = func(value)
            return ele
        else:
            raise NameError(
                "Please enter the correct targeting elements,"
                "'id','name','class','text','xpath','css'.")

    def find_elements(self, locator, parent=None):
        """Find element by locator, from html body or parent element.

        :param locator:  定位方式(by, value)
        :param parent:   父元素
               默认--从HTML根节点开始查找，全局查找
               指定--从元素的子类开始查找，作用域内查找
        """

        by, value = locator
        father = parent or self.web_driver
        gps = {
            "id": father.find_elements_by_id,
            "name": father.find_elements_by_name,
            "class": father.find_elements_by_class_name,
            "text": father.find_elements_by_link_text,
            "text_part": father.find_elements_by_partial_link_text,
            "xpath": father.find_elements_by_xpath,
            "css": father.find_elements_by_css_selector,
            "tag": father.find_elements_by_tag_name
        }
        func = gps.get(by)
        if func:
            ele_list = func(value)
            return ele_list
        else:
            raise NameError(
                "Please enter the correct targeting elements,"
                "'id','name','class','text','xpath','css'.")

    def wait_element(
            self, element, condition=Condition.visible, seconds=30):
        """等待元素在指定的时间内出现

        :param element:      元素的定位表达式
        :param condition:    等待方式
        :param seconds:      等待的时间
        :return:
        """

        by, value = element
        gps = {
            "id": (By.ID, value),
            "name": (By.NAME, value),
            "class": (By.CLASS_NAME, value),
            "text": (By.LINK_TEXT, value),
            "text_part": (By.PARTIAL_LINK_TEXT, value),
            "xpath": (By.XPATH, value),
            "css": (By.CSS_SELECTOR, value),
            "tag": (By.TAG_NAME, value)
        }
        locator = gps.get(by)
        if locator:
            ele = WebDriverWait(self.web_driver, seconds, 0.1,
                                (StaleElementReferenceException,)).until(
                condition(locator), message="by: %s, value: %s" % (by, value),
            )
            return ele
        else:
            raise NameError(
                "Please enter the correct targeting elements,"
                "'id','name','class','text','xpath','css'.")

    # def wait_with_parent(self, element, seconds=30, condition=Condition.visible, parent=None):
    #     by, value = element
    #     gps = {
    #         "id": (By.ID, value),
    #         "name": (By.NAME, value),
    #         "class": (By.CLASS_NAME, value),
    #         "text": (By.LINK_TEXT, value),
    #         "text_part": (By.PARTIAL_LINK_TEXT, value),
    #         "xpath": (By.XPATH, value),
    #         "css": (By.CSS_SELECTOR, value),
    #         "tag": (By.TAG_NAME, value)
    #     }
    #     locator = gps.get(by)
    #     ele = WebDriverWait(self.web_driver, seconds, 0.1,
    #                         (StaleElementReferenceException,)).until(element_by_parent(locator, parent=parent),message="by: %s, value: %s" % (by, value),
    #     )
    #     return ele

    def wait_not_element(
            self, element, condition=Condition.visible, seconds=30):
        """等待元素在指定的时间内消失

        :param element:      元素的定位表达式
        :param condition:    等待方式
        :param seconds:      等待的时间
        :return:
        """

        by, value = element
        gps = {
            "id": (By.ID, value),
            "name": (By.NAME, value),
            "class": (By.CLASS_NAME, value),
            "text": (By.LINK_TEXT, value),
            "text_part": (By.PARTIAL_LINK_TEXT, value),
            "xpath": (By.XPATH, value),
            "css": (By.CSS_SELECTOR, value),
            "tag": (By.TAG_NAME, value)
        }
        locator = gps.get(by)
        if locator:
            ele = WebDriverWait(self.web_driver, seconds, 0.1,
                                (StaleElementReferenceException,)).until_not(
                condition(locator), message="by: %s, value: %s" % (by, value),
            )
            return ele
        else:
            raise NameError(
                "Please enter the correct targeting elements,"
                "'id','name','class','text','xpath','css'.")

    def wait_elements(
            self, element, condition=Condition.visible_all, seconds=30):
        """等待元素在指定的时间类出现，并且可点击

        :param element:      元素的定位表达式
        :param condition:    等待方式
        :param seconds:      等待的时间
        :return:
        """

        by, value = element
        gps = {
            "id": (By.ID, value),
            "name": (By.NAME, value),
            "class": (By.CLASS_NAME, value),
            "text": (By.LINK_TEXT, value),
            "text_part": (By.PARTIAL_LINK_TEXT, value),
            "xpath": (By.XPATH, value),
            "css": (By.CSS_SELECTOR, value),
            "tag": (By.TAG_NAME, value)
        }
        locator = gps.get(by)
        if locator:
            ele_list = WebDriverWait(self.web_driver, seconds, 0.01,
                                     (StaleElementReferenceException,)).until(
                condition(locator)
            )
            return ele_list
        else:
            raise NameError(
                "Please enter the correct targeting elements,"
                "'id','name','class','text','xpath','css'.")

    def send_keys(self, ele, value):
        """输入文本

        :param ele:         元素
        :param value:       输入值
        :return:
        :usage: Send_keys(['id','element'],value)
        """

        self.get_screen_shot(element=ele, value=value)
        ele.send_keys(Keys.CONTROL, 'a')
        ele.send_keys(value)

    def clear_keys(self, ele):
        """清除文本

        :param ele:     元素
        :return:
        :usage: Send_keys(['id','element'],value)
        """

        self.get_screen_shot(element=ele)
        ele.clear()

    def click(self, ele):
        """功能：点击

        :param ele: 元素
        :return:
        :usage: click(ele,value)
        """

        self.get_screen_shot(element=ele)
        ele.click()

    def right_click(self, ele):
        """功能：右击

        :param ele: 元素
        :return:
        """

        self.get_screen_shot(element=ele)
        ActionChains(self.web_driver).context_click(
            ele.perform())

    def move_to_element(self, ele):
        """功能：移动到元素

        :param ele: 元素
        :return:
        """

        self.get_screen_shot(element=ele)
        ActionChains(self.web_driver).move_to_element(
            ele).perform()

    def move_and_click(self, ele):
        """功能：某些按钮，需要先移动到按钮才可以点击

        :param ele:
        :return:
        """

        self.get_screen_shot(element=ele)
        actions = ActionChains(self.web_driver)
        actions.move_to_element(ele)
        time.sleep(1)
        actions.click(ele)
        actions.perform()

    def double_click(self, ele):
        """功能：双击元素

        :param ele: 元素
        :return:
        """

        self.get_screen_shot(element=ele)
        ActionChains(self.web_driver).double_click(
            ele).perform()

    def drag_and_drop(self, ele, ele1):
        """功能：拖拽元素

        :param ele:     起始元素
        :param ele1:    终了元素
        :return:
        """

        self.get_screen_shot(element=ele)
        self.get_screen_shot(element=ele1)
        ActionChains(self.web_driver).drag_and_drop(
            ele, ele1).perform()

    def focus(self, ele):
        """功能:将光标或焦点定位至元素

        :param ele:
        :return:
        """

        self.get_screen_shot(element=ele)
        self.web_driver.execute_script(
            "arguments[0].scrollIntoView();", ele)

    def get_attribute(self, ele, value):
        """功能：得到元素的属性值

        :param ele:    元素
        :param value:  属性名称
        :usage: get_attribute(['id','element'],'attribute')
        :return:
        """

        self.get_screen_shot(element=ele)
        return ele.get_attribute(value)

    def get_text(self, ele):
        """获取文本

        :param ele:      元素
        :return:         返回的是元素的文本值
        :usage: get_text(ele)
        """

        self.get_screen_shot(element=ele)
        return ele.text

    def is_element_exists(self, ele):
        """判断元素是否存在

        :param ele:      元素
        :return:         返回True/False
        """
        try:
            self.wait_element(ele, seconds=5)
            return True
        except Exception:
            return False

    def submit(self, element):
        """功能：提交特定的表单

        :param element:   元素表达式
        :return:
        """

        ele = self.wait_element(element)
        self.get_screen_shot(element=ele)
        ele.submit()

    def select_by_value(self, ele, value):
        """功能：通过value选择下拉列表，必须是Select类型的下拉框才能使用

        :return
        :usage: select_by_value(ele,value)
        """

        self.get_screen_shot(element=ele)
        Select(ele).select_by_value(value)

    def select_by_text(self, ele, value):
        """功能：通过值选择下拉列表，必须是Select类型的下拉框才能使用

        :return
        :usage: select_by_text(['id','element'],value)
        """

        self.get_screen_shot(element=ele)
        Select(ele).select_by_visible_text(value)

    def select_by_index(self, ele, value):
        """功能：通过index值选择下拉列表，必须是Select类型的下拉框才能使用

        :return
        :usage: select_by_index(['id','element'],value)
        """

        self.get_screen_shot(element=ele)
        Select(ele).select_by_index(value)

    def select_by_partial_text(self, ele, text):
        """功能：通过部分匹配值选择下接列表

        :param ele:
        :param text:
        :return:
        """
        self.get_screen_shot(element=ele)
        Select(ele).select_by_partial_text(text)
