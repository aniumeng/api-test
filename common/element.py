#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from common.action import ActionBase
from common.action import Condition
from common.utility import CloudConf, WebDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from common.el_select import Select
from common.decorators import retry_on_exception
import logging
import time

log = logging.getLogger(__name__)


def get_result(message):
    unknown = u"X_X"
    res = unknown
    ret_tuple = [
        (u'el-icon-success', u"成功"),
        (u'cel-icon-error', u"成功"),
        (u'el-message_icon el-icon-failed', u"失败"),
        (u"el-message__icon el-icon-error", u"失败"),
        ("icon-alert-error", "失败"),
        ("el-icon-undefined", "失败"),
        (u'el-dialog__header', u"成功"),
        (u"el-icon-info", "告警"),
        ('icon-alert-success', "提示成功"),
        (u'salus-global-alert', u"告警")]
    for key, value in ret_tuple:
        if key in message:
            res = value
            break
    if res == unknown:
        log.warning(u"%s未记录的结果状态类型:%s" % (unknown, message))
    return res


def get_alert_mark(driver, global_only=False, time_out=310):
    """等待中间提示框出现,并返回结果

    :param driver:
    :param global_only: T仅等待alert提示,F等待alert和dialog提示
    :param time_out:    等待出现的超时时间
    """
    log.info(u"等待弹框提示.........")
    end = time.time() + time_out
    while time.time() < end:
        try:
            alert_all = './/div[@role="alert" or @role="dialog"]'
            alert_glb = './/div[@role="alert"]'
            alert_path = alert_glb if global_only else alert_all
            alerts = driver.web_driver.find_elements_by_xpath(alert_path)
            alerts = list(filter(lambda x: x.is_displayed(), alerts))
            if not any(alerts):
                continue
            alert = alerts[0].get_attribute("innerHTML")
            if 'el-message' not in alert:
                mark = alerts[0].text.replace("\n", " ")
            else:
                mark = alerts[0].text
            result = get_result(alert)
            result = u" ".join([result, mark])
            log.info(result)
            return result
        except StaleElementReferenceException as e:
            log.debug(e)


def retriable(func):
    @wraps(func)
    def retry(self, *args, **kwargs):
        retry_times = 0
        while retry_times < 3:
            try:
                res = func(self, *args, **kwargs)
                return res
            except Exception as e:
                logging.info("Retrying Func %s in 5sec, Remain Times %s, cause : %s", func.__name__,
                             3 - retry_times, e)
                self.driver.web_driver.refresh()
                retry_times += 1
                if retry_times >= 3:
                    logging.error("Func %s Failed after %s times retry", func.__name__, retry_times)
                    raise e
                time.sleep(5)

        return func(*args, **kwargs)
    return retry


class Element(object):
    """元素标签基类"""
    def __init__(self, locator, parent=None):
        self.parent = parent
        self.locator = locator
        self.driver = ActionBase()
        self.ele = None
        self.find_element()

    def find_element(self):
        start, expired = time.time(), False
        while not expired:
            try:
                self.ele = self.driver.find_element(
                    locator=self.locator, parent=self.parent
                )
                break
            except NoSuchElementException as e:
                log.debug(e)
                expired = time.time() - start > 60
                if expired:
                    raise e

    def attribute(self, attr):
        return self.driver.get_attribute(self.ele, attr)


class Elements(object):
    """元素标签组基类"""
    def __init__(self, locator, parent=None):
        self.parent = parent
        self.locator = locator
        self.driver = ActionBase()
        self.ele = None
        self.find_elements()

    def find_elements(self):
        self.ele = self.driver.find_elements(
            locator=self.locator, parent=self.parent
        )

    def texts(self):
        texts = [self.driver.get_text(ele) for ele in self.ele]
        return texts

    def attributes(self, attribute):
        attr = [self.driver.get_attribute(ele, attribute)
                for ele in self.ele]
        return attr


class CheckBox(Element):
    """CheckBox：复选框"""
    def __init__(self, text=None, locator=None, parent=None):
        if text is not None:
            self.text = text
            xpath = './/label[contains(., "%s")]/parent::div//input' % text
            locator = ('xpath', xpath)
        else:
            locator = locator
        super(CheckBox, self).__init__(locator, parent)

    @property
    def enabled(self):
        """可能没用了，暂时留着"""
        ok = self.ele.is_enabled()
        return ok

    @property
    def is_checked(self):
        xpath = './parent::span'
        ck = Element(('xpath', xpath), parent=self.ele)
        if 'checked' in ck.attribute('class'):
            return True
        else:
            return False

    def on(self):
        """勾选动作"""
        self.driver.click(self.ele)


class Label(Element):
    def __init__(self, locator=None, text=None, parent=None):
        if locator is None and text is not None:
            locator = ('xpath', './/label[contains(., "%s")]/parent::div' % text)
        super(Label, self).__init__(locator, parent)

    def text(self):
        return self.driver.get_text(self.ele)

    def on(self, locator=None):
        """选取动作，使用没有任何说明的勾选"""
        xpath = locator or ("xpath", ".//input")
        Button(locator=xpath, parent=self.ele).click()

    @property
    def is_checked(self,):
        xpath = ('xpath', './/label')
        ck = Element(xpath, parent=self.ele)
        if 'checked' in ck.attribute('class'):
            return True
        else:
            return False

    def check(self):
        xpath = './parent::div//div[@class="help-block"]'
        ele = Label(('xpath', xpath), parent=self.ele)
        return ele.text()


class SpanLabel(Label):

    def __init__(self, text, parent=None):
        locator = ('xpath', './/span[normalize-space(text())="%s"]/'
                            'parent::label' % text)
        super(Label, self).__init__(locator, parent)

    def on(self):
        self.ele.click()

    @property
    def is_checked(self):
        if 'checked' in self.ele.get_attribute('class'):
            return True
        else:
            return False


class Button(Element):
    """Button: 可点击按钮"""
    def __init__(self, locator=None, text=None, parent=None):
        self.wait_time = 30
        if locator is None:
            xpath = ".//span[normalize-space(text())='%s']/parent::button" % text
            locator = ('xpath', xpath)
        super(Button, self).__init__(locator, parent)

    def click(self):
        self.__wait_click_enable()
        self.driver.click(self.ele)

    def wait_click_enabled(self):
        self.__wait_click_enable()

    def __wait_click_enable(self):
        if self.parent is None:
            self.driver.wait_element(
                element=self.locator,
                condition=Condition.click_enable,
                seconds=self.wait_time
            )
        else:
            start = time.time()
            while time.time() < start + self.wait_time:
                enabled = self.ele.is_enabled()
                if enabled:
                    break
                else:
                    time.sleep(1)


class A(Element):
    """a标签: 可点击"""
    def __init__(self, locator=None, text=None, parent=None):
        self.wait_time = 30
        if locator is None:
            xpath = ".//a[normalize-space(text())='%s']" % text
            locator = ('xpath', xpath)
        super(A, self).__init__(locator, parent)

    def click(self):
        # self.__wait_click_enable()
        self.driver.click(self.ele)

class Input(Element):
    """Input: 普通的输入框"""
    def __init__(self, locator, parent=None):
        super(Input, self).__init__(locator, parent)

    def input(self, text):
        """输入动作"""
        self.driver.send_keys(self.ele, text)

    def clear(self):
        """清空输入框"""
        self.driver.clear_keys(self.ele)
        time.sleep(0.8)

    # def check(self):
    #     xpath = './ancestor::div//div[@class="help-block"]'
    #     ele = Label(('xpath', xpath), parent=self.ele)
    #     return ele.text()


class RawInput(Element):
    """RawInput: 带标签说明的输入框"""
    def __init__(self, text, parent=None):
        self.text = text
        xpath = './/label[contains(., "%s")]/parent::div' % text
        super(RawInput, self).__init__(('xpath', xpath), parent)

    def input(self, text):
        """输入动作"""
        xpath = './/input'
        ele = Element(locator=('xpath', xpath), parent=self.ele).ele
        self.driver.send_keys(ele, text)

    def multi_input(self, texts):
        """多行文本输入动作"""
        if len(texts) == 1:
            self.input(texts[0])
        else:
            input_path = ".//input"
            add_path = ".//a[contains(@class, 'add')]"
            for index, text in enumerate(texts):
                inputs = Elements(locator=('xpath', input_path),
                                  parent=self.ele).ele
                self.driver.send_keys(inputs[-1], text)
                if len(texts) - index > 1:
                    Button(locator=('xpath', add_path), parent=self.ele).click()

    def deinput_all(self):
        """多行文本全删除"""
        del_path = ".//a[contains(@class, 'btn_delete')]"
        del_els = Elements(locator=('xpath', del_path), parent=self.ele).ele
        for del_el in del_els[:0:-1]:
            del_el.click()
            dl = ('xpath', './/body/div[@role="dialog"][@aria-label="操作提示"]')
            Dialog(locator=dl).confirm(wait=False)

    def input_by_id_js(self, id_element, text):
        """通过js和id输入"""
        self.driver.input_by_id_js(id_element=id_element, value=text)

    def clear(self):
        """清空输入框"""
        self.driver.clear_keys(self.ele)
        time.sleep(0.1)


class Table(Element):
    """表视图"""
    def __init__(self, parent=None, locator=None):
        self.locator_table = \
            locator or ('xpath',
                        ".//div[contains(@class,'el-table--fit')]")
        super(Table, self).__init__(self.locator_table, parent)
        self.status_key = u"状态"      # 状态列表头字段，子类可以覆盖
        # self.perform_refreshing()
        self.locator_head_row = ('xpath', './/thead/tr/th//div')
        self.locator_table_row = ('xpath', './/tbody/tr')
        self.locator_row_cell = ('xpath', './td')
        self.locator_foot = ('xpath', './/tfoot')

    @property
    def info(self):
        try_times = 5
        for i in range(try_times):
            try:
                content = list()
                heads = self.get_table_head()
                body = self.get_table_body()
                for row in body:
                    content.append(dict(zip(heads, row)))
                return content
            except StaleElementReferenceException as e:
                log.debug(e)
                log.info("table stale...")
                self.find_element()
                self.perform_refreshing()
                continue
        return list()

    def row_status(self, name, name_key=u"ID/名称"):
        """返回实例状态

        :param name:        实例名称
        :param name_key:    名称字段键
        :return:     None -- 实例不存在
                     string -- 状态字段
        """

        row = list(filter(lambda x: name == x.get(name_key), self.info))
        if any(row):
            status = row[0][self.status_key]
        else:
            status = None
        return status

    def set_max_rows(self):
        """设置页脚，显示最大行数"""
        for i in range(3):
            try:
                sel = Selector(locator=('xpath', './/input[@placeholder="请选择"]'))
                last = len(sel.options)
                sel.select_index(last - 1)
                # foot = Element(locator=self.locator_foot, parent=self.ele)
                # sel_loc = ('xpath', './/select')
                # footers = Elements(locator=sel_loc, parent=foot.ele)
                # if any(footers.ele):
                #     sel = Selector(locator=sel_loc, parent=foot.ele)
                #     last = len(sel.options)
                #     sel.select_index(last - 1)
                break
            except StaleElementReferenceException as e:
                log.info(u"set max row stale")
                log.debug(e)

    def get_table_head(self):
        locator_head_row = ('xpath', './/thead[@class="has-gutter"]/tr/th//div')
        cells = Elements(locator_head_row, parent=self.ele)
        # locator = ('xpath', './/div[@class="el-table__fixed"]//table')
        # cell_1 = Elements(locator, parent=self.ele).texts()[0]
        # log.info(cell_1)
        if 'span' in cells.ele[0].get_attribute('innerHTML'):
            text1 = cells.ele[0].get_attribute('innerHTML').split('<', 1)[0]
        elif '<' not in cells.ele[0].get_attribute('innerHTML'):
            text1 = cells.ele[0].get_attribute('innerHTML')
        else:
            text1 = cells.ele[0].text
        texts = cells.texts()
        texts = list(filter(lambda x: len(x) != 0, texts))
        if text1 is not None:
            texts.insert(0, text1)
        texts = list(filter(lambda x: len(x) != 0, texts))
        text_sets = list(set(texts))
        text_sets.sort(key=texts.index)
        # return texts
        return text_sets

    def get_table_body(self):
        locator_table_row = ('xpath', './div[3]//tbody/tr')
        rows = Elements(locator_table_row, parent=self.ele).ele
        row_list = list()
        if len(rows) < 1:   # 表为空的情况
            return row_list
        for row in rows:
            row_info = list()
            columns = Elements(self.locator_row_cell, parent=row).ele
            # # td[2]名称栏
            # name_id = columns[1].text
            # if name_id is not None and len(name_id) > 0:
            #     name = name_id.split()[-1].strip()
            # else:
            #     name = name_id
            # td[0] 名称栏
            if 'a' in columns[0].get_attribute('innerHTML'):
                coumn0 = Button(locator=('xpath', './/span/a'),
                                parent=columns[0])
                name = coumn0.ele.get_attribute('innerHTML').strip()
            else:
                name = columns[0].text.strip()
            if name is not None:
                row_info.append(name)
            # td[1->]其他
            cells = columns[1:]
            [row_info.append(cell.text) for cell in cells]
            row_list.append(row_info)
        return row_list

    def perform_refreshing(self, start_timeout=3, load_timeout=120):
        log.debug("wait page table_refreshing...")
        self.__wait_table_loader_start(timeout=start_timeout)
        self.__wait_table_loader_end(timeout=load_timeout)

    def __wait_table_loader_start(self, timeout=3):
        """等待刷新&加载过程中列表蒙层出现"""
        start = time.time()
        expire = False
        count = 0
        while not expire:
            empty = self.is_requesting_empty()
            expire = time.time() > (start + timeout)
            if not empty:
                count += 1
                log.debug(u"load started, cost times try %s" % count)
                break
        log.debug(u"load started, timeout %s" % (time.time() - start))

    def __wait_table_loader_end(self, timeout=120):
        """等待刷新&加载过程中列表蒙层消失"""
        start = time.time()
        expire = False  # 是否超时
        while not expire:
            empty = self.is_requesting_empty()
            expire = time.time() > (start + timeout)
            if empty:
                log.debug(u"load ended, cost time %s" % (time.time() - start))
                break
        log.debug(u"load ended, timeout %s" % (time.time() - start))

    def is_requesting_empty(self):
        load_loc = '//tr[@is-requesting="isRequesting"]/*'
        loadings = self.driver.find_elements(
            locator=('xpath', load_loc), parent=self.ele)
        log.debug("child count=%s, child=%s" % (len(loadings), loadings))
        empty = (not any(loadings))
        return empty


class TableRow(Element):
    """表行元素"""
    def __init__(self, name, parent=None, row_path=None):
        # self.row_xpath = row_path or './/*[text()="%s"]/ancestor::tr' % name
        # self.row_xpath = row_path or './/span[text()="%s"]ancestor::div[starts-with(@class,"el-table el-table--fit")]' % name
        self.row_xpath = row_path or ".//div[contains(@class,'el-table--fit')]"
        self.locator_row = ('xpath', self.row_xpath)
        self.name = name
        super(TableRow, self).__init__(self.locator_row, parent)

    def go_detail(self, locator=None):
        log.debug("go resource detail")
        # locator_id = locator or ('xpath', './td[1]/div/button')
        # detail_xpath = './/div[@class="el-table__fixed"]//a[contains(text(), "%s")]' % self.name
        detail_xpath = './/div[@class="el-table__fixed"]//a[normalize-space(text())="%s"]' % self.name
        locator_id = locator or ('xpath', detail_xpath)
        id_href = A(locator_id, parent=self.ele)
        id_href.click()
        time.sleep(1)

    def check_row(self, locator=None):
        locator_box = locator or ('xpath', './td[0]//input')
        box = Button(locator_box, parent=self.ele)
        box.click()

    def do_action(self, text):

        more_path = './/div[@class="el-table__fixed-right"]//a[normalize-space(text())="%s"]/ancestor::tr/td[last()]' % self.name
        # more_path = './ancestor::tr/td[last()][not(contains(@class, "hidden"))]/div'
        more_ele = Element(('xpath', more_path), parent=self.ele)
        # Elements(('xpath', more_path), parent=self.ele)
        # xpath = './/button/span[contains(text(), "%s")]' % text
        xpath = './/button/span[normalize-space(text())="%s"]' % text
        bu = Button(('xpath', xpath), parent=more_ele.ele)
        bu.click()

    # def more(self):
    #     """点击更多按钮"""
    #     more_path = './td[last()]/div'
    #     t_out = time.time() + 30
    #     expire = False
    #     while not expire:
    #         expire = time.time() > t_out
    #         try:
    #             ele = Label(("xpath", more_path), parent=self.ele)
    #             text = ele.text()
    #             log.debug(text)
    #             if len(text) > 1:
    #                 break
    #             else:
    #                 time.sleep(0.5)
    #         except StaleElementReferenceException as e:
    #             log.debug(e)
    #     locator_more = ('xpath', more_path)
    #     more_ele = Button(locator_more, parent=self.ele)
    #     more_ele.click()
    #
    # def more_action(self, text, action='click'):
    #     """操作更多一级菜单
    #
    #     :param text:   一级菜单名
    #     :param action: 操作动作
    #         click -- 点击
    #         move  -- 移动到
    #     :return:
    #     """
    #
    #     xpath = './/actions/action-list/ul/li/a//' \
    #             'span[contains(text(), "%s")]' % text
    #     more_ele = Element(('xpath', xpath), parent=self.ele)
    #     if action == 'click':
    #         self.driver.click(more_ele.ele)
    #     else:
    #         self.driver.move_to_element(more_ele.ele)

    def get_row_texts(self):
        """获取row内容

                :param
                :return:
                """

        more_ele = Elements(('xpath', self.row_xpath), parent=self.ele)
        return more_ele.texts()

    def more_list(self):
        """更多一级菜单列表

        :param
        :return:
        """

        xpath = './/actions/action-list/ul/li/a//span'
        more_ele = Elements(('xpath', xpath), parent=self.ele)
        return more_ele.texts()

    def more_action_action(self, text, text1):
        """操作更多二级菜单

        :param text:  一级菜单名
        :param text1: 二级菜单名
        :return:
        """

        xpath1 = './/actions/action-list/ul/li/a//' \
                 'span[contains(text(), "%s")]' % text
        xpath2 = './/actions/action-list/ul/li/a//' \
                 'span[contains(text(), "%s")]/ancestor::li/ul//' \
                 'span[contains(text(), "%s")]' % (text, text1)
        more1 = Element(('xpath', xpath1), parent=self.ele)
        self.driver.move_to_element(more1.ele)
        more2 = Element(('xpath', xpath2), parent=self.ele)
        self.driver.focus(more2)
        self.driver.click(more2.ele)

    def do_more_action_action(self, act, act1):
        """操作更多二级菜单

        :param act:  一级菜单名
        :param act1: 二级菜单名
        :return:
        """
        self.do_action(text="更多")
        time.sleep(0.1)
        self.more_action_action(text=act, text1=act1)


class TextArea(Element):
    """RawInput: 带标签说明的多行输入框"""
    def __init__(self, text, parent=None):
        self.text = text
        xpath = './/label[contains(., "%s")]/parent::div//textarea' % text
        super(TextArea, self).__init__(('xpath', xpath), parent)

    def input(self, text):
        """输入动作"""
        self.driver.send_keys(self.ele, text)

    def set_value_by_js(self, id_element, text):
        """执行js"""
        self.driver.input_by_id_js(id_element, text)


class Selector(Element):
    """selector: 单项选取器"""
    def __init__(self, locator, count=0, parent=None):
        super(Selector, self).__init__(locator, parent)
        self.wait_options(count)

    @property
    def options(self):
        """获取选项元素列表"""
        opt = Select(self.ele).options
        return opt

    def wait_options(self, count=0, time_out=60):
        """等待option数量大于count"""
        log.debug("wait selector loading...")
        t_out = time.time() + time_out
        expire = False
        while not expire:
            try:
                expire = time.time() > t_out
                if len(self.options) > count:
                    break
                # if len(self.options) == 1:
                #     valid_opt = filter(
                #         lambda x: (
                #             len(x) != 0) and (
                #             x != u"?") and (
                #             u"选择" not in x),
                #         self.texts)
                #     if any(valid_opt):
                #         break
                # elif len(self.options) >= count:
                #     log.debug("000000")
                #     break
            except StaleElementReferenceException as e:
                log.debug(e)

    @property
    def texts(self):
        """获取选项文本列表"""
        items = [option.text for option in self.options]
        return items

    def select_value(self, value):
        """via option attribute： value='x-x-x'"""
        self.driver.select_by_value(self.ele, value)

    def select_text(self, text):
        """via option visible text: >'x-x-x'<"""
        self.driver.select_by_text(self.ele, text)

    def select_index(self, index):
        """via option index: order"""
        self.driver.select_by_index(self.ele, index)

    # def select_partial_text(self, text):
    #     """via option visible text contains text: >'pre__x-x-x__post'<"""
    #     opts = self.texts
    #     found = False
    #     for i in range(len(opts)):
    #         if text in opts[i]:
    #             self.select_index(i)
    #             found = True
    #             break
    #     # found or log.info(self.texts)
    #     assert found, self.texts

    def select_partial_text(self, text):
        """via option visible text contains text"""
        self.driver.select_by_partial_text(self.ele, text)

    def select_text_with_bracketed(self, text):
        """via option visible text contains text: >'x-x-x(post)'<"""
        opts = self.texts
        found = False
        for i in range(len(opts)):
            if text == opts[i].split('(')[0]:
                found = True
                self.select_index(i)
                break
        assert found, self.texts

    def check(self):
        xpath = './ancestor::div//div[@class="help-block"]'
        ele = Label(('xpath', xpath), parent=self.ele)
        return ele.text()


class LabelRadio(Element):
    """Radio: 选择项，外层为label的radio按钮"""
    def __init__(self, text, parent=None):
        self.text = text
        xpath = './/label[contains(., "%s")]/' \
                'span[contains(@class, "input")]' % text
        super(LabelRadio, self).__init__(('xpath', xpath), parent)

    @property
    def enabled(self):
        ok = self.ele.is_enabled()
        return ok

    @property
    def is_checked(self, ):
        xpath = ('xpath', './parent::label')
        ck = Element(xpath, parent=self.ele)
        if 'checked' in ck.attribute('class'):
            return True
        else:
            return False

    def on(self):
        """选取动作"""
        self.driver.click(self.ele)

    def check(self):
        xpath = './ancestor::div//div[@class="help-block"]'
        ele = Label(('xpath', xpath), parent=self.ele)
        return ele.text()


class RawSelector(Selector):
    """Selector: 单项选取器 可以通过说明标签定位"""
    def __init__(self, text, count=0, parent=None):
        self.text = text
        xpath = './/label[contains(., "%s")]/parent::div//' \
                'div[@class="el-select el-select--small"]//input' % text
        super(RawSelector, self).__init__(
            locator=('xpath', xpath), count=count, parent=parent)


class ResourceSearch(Element):
    """资源搜索"""

    def __init__(self, search_type=None, parent=None):
        """搜索

        :param search_type: 类型,比如云服务器中类型
        :param parent:
        """

        self.locator = ('xpath', './/div[contains(@class, "sc-search")]')
        self.search_type = search_type
        super(ResourceSearch, self).__init__(self.locator, parent)

    def find_element(self):
        self.ele = self.driver.wait_element(
            element=self.locator, condition=Condition.visible,
            seconds=60
        )

    def search(self, name):
        """查找：非自动筛选

        :param name: 要搜索的名称
        :return:
        """

        if self.search_type is not None:
            self.set_search_type(self.search_type)
        self.set_filter_name(name)
        auto = self._set_autocomplete(name)
        if auto is False:
            ele = Button(('xpath', './/i'), parent=self.ele)
            ele.click()
        time.sleep(0.8)
        self.__wait_table_loader_end(timeout=30)

    def set_search_type(self, search_type, locator=None):
        locator_id = locator or ('xpath', './/select[@ng-if="filterFacets"]')
        sel = Selector(locator_id, parent=self.ele)
        sel.select_text(search_type)

    def set_filter_name(self, name, locator=None):
        locator_xpath = locator or ('xpath', './/input')
        ele = Input(locator_xpath, parent=self.ele)
        ele.input(name)
        time.sleep(0.8)

    def click_search(self, name, locator=None):
        """查找：需要主动触发搜索"""
        if self.search_type is not None:
            self.set_search_type(self.search_type)
        self.set_filter_name(name)
        locator_xpath = locator or (
            'xpath', './/span[@class="input-group-addon"]')
        ele = Button(locator_xpath, parent=self.ele)
        ele.click()

    def __wait_table_loader_end(self, timeout=10):
        """等待刷新&加载过程中列表蒙层消失"""
        load_loc = './/div[contains(@class, "el-loading-mask")]'
        self.driver.wait_not_element(element=('xpath', load_loc), seconds=timeout)

    def _set_autocomplete(self, name):
        # :todo 临时修改，下接框有自动补全
        # classname = 'el-autocomplete-suggestion'
        # ele = Element(locator=('class', classname))
        # ss = Elements(locator=('xpath', './/ul/li'), parent=ele.ele)
        # if len(ss.ele) > 1:
        #     for x in ss.ele:
        #         if name == x.text:
        #             x.click()
        #             return True
        # else:
        return False


class Page(object):
    """页面对象，对于一种资源的页面"""
    def __init__(self, locator=None):
        self.driver = ActionBase()
        self.ele = None
        self.locator = locator or ('class', 'kcmp-content-container')
        # self.go_to_page()
        # self.perform_refreshing()

    @property
    def url(self):
        uri = '/'
        return uri

    # @retriable
    @retry_on_exception(tries=3, delay=1, backoff=2, max_delay=30)
    def go_to_page(self):
        # todo 定位问题
        log.error("url%s", self.url)
        url_abs = CloudConf().url + self.url
        log.error("urlabs%s", url_abs)
        # self.driver.f5()
        # if self.driver.get_url() != url_abs:

        self.driver.get(url_abs)
        try:
            self.find_element()
        except TimeoutException:
            # time.sleep(5)
            self.driver.web_driver.refresh()
            #retry后重试刷新,页面id不一致，导致元素定位不到失败
            self.driver.wait_element(element=self.locator, seconds=5)
            self.find_element()

        # log.info('等刷新')
        try:
            self.perform_refreshing()
        except TimeoutException:
            # time.sleep(5)
            self.driver.web_driver.refresh()
            time.sleep(5)
            self.perform_refreshing()

    def find_element(self):
        self.ele = self.driver.wait_element(
            element=self.locator, condition=Condition.visible,
            seconds=60
        )

    # def hint(self, locator=None):
    #     locator = locator or ('xpath', '//div[@class="help-hint col-xs-12"]/p')
    #     label = Label(locator, parent=self.ele)
    #     return label.text()
    # @retriable
    @retry_on_exception(tries=3, delay=1, backoff=2, max_delay=30)
    def trigger_create(self, text=None, locator=None):
        if text is not None:
            locate = ('xpath', '//span[normalize-space(text())="%s"]/parent::button' % text)
        else:
            locate = locator or \
                     ('xpath', './/button[contains(@class, "btn-primary")]')
        self.driver.wait_element(element=locate, seconds=90)
        create = Button(locate, parent=self.ele)
        create.click()

    def __wait_table_loader_start(self, timeout=5):
        """等待刷新&加载过程中列表蒙层出现"""
        start = time.time()
        expire = False
        count = 0
        while not expire:
            empty = self.is_requesting_empty()
            expire = time.time() > (start + timeout)
            if not empty:
                count += 1
                log.debug(u"load started, cost times try %s" % count)
                break
        log.debug(u"load started, timeout %s" % (time.time() - start))

    def __wait_table_loader_end(self, timeout=120):
        """等待刷新&加载过程中列表蒙层消失"""
        load_loc = './/div[contains(@class, "el-loading-mask")]'
        self.driver.wait_not_element(element=('xpath', load_loc), seconds=timeout)
        # start = time.time()
        # expire = False  # 是否超时
        # while not expire:
        #     empty = self.is_requesting_empty()
        #     expire = time.time() > (start + timeout)
        #     if empty:
        #         log.debug(u"load ended, cost time %s" % (time.time() - start))
        #         break
        # log.debug(u"load ended, timeout %s" % (time.time() - start))

    def is_requesting_empty(self):
        load_loc = './/div[contains(@class, "el-loading-mask")]'
        try:
            self.driver.wait_element(element=('xpath', load_loc), seconds=5)
        except TimeoutException:
            return False
        # loadings = self.driver.find_elements(
        #     locator=('xpath', load_loc), parent=self.ele)
        # log.info("child count=%s, child=%s" % (len(loadings), loadings))
        # empty = (not any(loadings))
        # return empty

    def perform_refreshing(self, start_timeout=5, load_timeout=120):
        log.debug("wait page table_refreshing...")
        self.__wait_table_loader_start(timeout=start_timeout)
        self.__wait_table_loader_end(timeout=load_timeout)

    # def wait_create_ok(self, name, status_func,
    #                    try_times=200, search_name=False):
    #     """等待创建完成
    #
    #     :param name:
    #     :param status_func:
    #     :param try_times: 默认200次(等价1800s)
    #            等待时间潮汐式增加，每五个一组。
    #     :param search_name: 是否在等待过程中进行搜索True|False
    #     :return:
    #     """
    #
    #     log.info("create, wait instance %s status..." % name)
    #     count, status = 0, None
    #     while count < try_times:
    #         self.go_to_page()
    #         if search_name is True:
    #             ResourceSearch().search(name)
    #         status = status_func(name)
    #         log.info("instance %s status=%s" % (name, status))
    #         if status in [u"正在运行", u"可用", u"锁定中", u"错误",
    #                       u"使用中", u"使用中（已挂满）", u'故障', u'失败', u"已挂起"]:
    #             break
    #         time.sleep(3 * (count % 5 + 1))
    #         count += 1
    #     return status
    #
    # def wait_delete_ok(self, name, status_func,
    #                    try_times=200, search_name=False):
    #     log.info("delete, wait instance %s status..." % name)
    #     count, status, delete_ok = 0, None, False
    #     while count < try_times:
    #         self.go_to_page()
    #         if search_name is True:
    #             ResourceSearch().search(name)
    #         status = status_func(name)
    #         log.info("instance %s status=%s" % (name, status))
    #         if status is None:
    #             delete_ok = True
    #             break
    #         elif (u"错误" in status) or (u"故障" in status):
    #             delete_ok = False
    #             break
    #         time.sleep(3 * (count % 5 + 1))
    #         count += 1
    #     return delete_ok
    #
    # def wait_status_as(self, name, status, status_func,
    #                    try_times=200, search_name=False):
    #     """等待状态变为
    #
    #     :param name:
    #     :param status:       预期状态(list、tuple、str)
    #     :param status_func:
    #     :param try_times:
    #     :param search_name
    #     :return:
    #     """
    #     log.info("Wait instance %s status as %s..." % (name, status))
    #     status_list = status if isinstance(
    #         status, (list, tuple)) else [status]
    #     count, c_status = 0, None
    #     while count < try_times:
    #         self.go_to_page()
    #         if search_name is True:
    #             ResourceSearch().search(name)
    #         c_status = status_func(name)
    #         log.info("instance %s status=%s" % (name, c_status))
    #         if c_status in status_list:
    #             break
    #         elif c_status in [u"错误", u'故障', u'失败']:
    #             break
    #         time.sleep(3 * (count % 5 + 1))
    #         count += 1
    #     return c_status

    def get_toast_mark(self, time_out=60, global_only=False):
        """等待中间提示框出现，并返回值"""
        # log.info("等待弹框提示...")
        return get_alert_mark(driver=self.driver, global_only=global_only,
                              time_out=time_out)
        # try:
        #     xpath = './/div[@role="alert"]'
        #     ele = self.driver.wait_element(('xpath', xpath), seconds=time_out)
        #     info = self.driver.find_element(('tag', 'p'), parent=ele).text
        #     success_icon = 'el-message_icon el-icon-success'
        #     mark = ele.get_attribute("innerHTML").replace(success_icon, u'成功', 1)
        #     log.info("弹框提示为: %s" % info)
        #     return mark
        # except (TimeoutException, StaleElementReferenceException) as e:
        #     log.debug(e)
        #     return None

    def wait_toast_away(self, time_out=20, global_only=False):
        self.driver.wait_not_element(element=('xpath', './/div[@role="alert" or @role="dialog"]'), seconds=time_out)


    @staticmethod
    def wait_delete_ok(name, status_func, try_times=50, appear_until=20):
        """

        :param name:
        :param status_func:
        :param try_times:
               等待时间潮汐式增加，每五个一组。
               一个完整涨潮周期为5次，合计 3x(0+1+2+3+4)=30s
               +------------+-------------+
               |  count (c) |    time(s)  |
               | 5          | 30          |
               | 10         | 60          |
               | 20         | 120         |
               | 50         | 300         |
               | 100        | 600         |
               | 150        | 900         |
               | 200        | 1200        |
               +------------+-------------+
        :param appear_until: 等N次状态任然为初始状态
        :return:
        """
        log.info(u"delete, wait resource %s status..." % name)
        count, status, delete_ok = 0, None, False
        init_status, init_count = None, 0
        while count < try_times:
            status = status_func(name)
            log.info(u"resource %s status=%s" % (name, status))
            if status is None:
                delete_ok = True
                break
            elif (u"错误" in status) or (u"故障" in status):
                delete_ok = False
                break
            if count == 0:
                init_status = status
            if status == init_status:
                init_count += 1
            else:
                init_count = 0
            if init_count > appear_until:
                log.info(u"wait %s, always be %s in %s serial times." % (
                    name, init_status, init_count))
                break
            time.sleep(3 * (count % 5 + 1))
            count += 1
        return delete_ok

    @staticmethod
    def wait_status_as(name, status, status_func,
                       try_times=50, appear_until=20):
        """等待状态变为

        :param name:
        :param status:       预期状态(list、tuple、str)
        :param status_func:
        :param try_times:
               等待时间潮汐式增加，每五个一组。
               一个完整涨潮周期为5次，合计 3x(0+1+2+3+4)=30s
               +------------+-------------+
               |  count (c) |    time(s)  |
               | 5          | 30          |
               | 10         | 60          |
               | 20         | 120         |
               | 50         | 300         |
               | 100        | 600         |
               | 150        | 900         |
               | 200        | 1200        |
               +------------+-------------+
        :param appear_until: N次内首次出现在列表中
        :return:
        """
        status_list = status if isinstance(
            status, (list, tuple)) else [status]
        status_str = u"[" + u",".join(status_list) + u"]"
        log.info(u"Wait resource %s status in %s..." % (name, status_str))
        count, c_status = 0, None
        count_none = 0  # if always be None for x times
        while count < try_times:
            c_status = status_func(name)
            log.info(u"resource %s status=%s" % (name, c_status))
            if c_status in status_list:
                break
            elif c_status in [u'故障', u'失败']:
                break
            status_none = status is None
            if status_none:
                count_none += 1
            else:
                count_none = 0
            if count_none > appear_until:
                log.info(u"wait %s, always be None in %s serial "
                         u"times." % (name, count_none))
                break
            time.sleep(3 * (count % 5 + 1))
            count += 1
        return c_status


class ModalView(Element):
    """创建页面基类"""
    def __init__(self, title, parent=None):
        modal_xpath = '//div[@class="sc-back-left"][contains(text(), "%s")]' \
                      '/ancestor::main/div' % title
        self.locator = ('xpath', modal_xpath)
        super(ModalView, self).__init__(self.locator, parent)

    def find_element(self):
        self.ele = self.driver.wait_element(
            element=self.locator, condition=Condition.visible)

    # def submit(self):
    #     log.debug("*.click modal create.")
    #     locator_create = ('xpath', self.modal_step % 'primary finish')
    #     create = Button(locator_create, parent=self.ele)
    #     create.click()

    def confirm(self, text="确定"):
        log.debug("*.click modal confirm.")
        # locator_confirm = ('xpath', self.modal_step % 'primary')
        confirm = Button(text=text, parent=self.ele)
        self.driver.focus(confirm.ele)
        confirm.click()
        time.sleep(0.8)


class Dialog(Element):
    """Dilog页面基类"""
    def __init__(self, title=None, parent=None, locator=None, is_exists=True):
        self.is_exists = is_exists
        if title is not None:
            modal_xpath = './/div[@role="dialog"][@aria-label="%s"]' % title
            self.locator = ('xpath', modal_xpath)
        else:
            self.locator = locator or ('xpath', './/div[@role="dialog"]')
        super(Dialog, self).__init__(self.locator, parent)

    def find_element(self):
        try:
            self.ele = self.driver.wait_element(element=self.locator, seconds=8)
            self.is_exists = True
        except Exception as e:
            log.info(e)
            self.is_exists = False
        # if self.is_exists is True:
        #     self.ele = self.driver.wait_element(
        #         element=self.locator, condition=Condition.visible)
        #     self.is_exists = True
        # else:
        #     try:
        #         self.ele = self.driver.wait_element(
        #             element=self.locator, condition=Condition.visible,
        #             seconds=5)
        #     except Exception:
        #         self.is_exists = False

    # def confirm(self, text="确定"):
    #     if self.is_exists is True:
    #         log.debug("*.click modal confirm.")
    #         locator = ('xpath', './/button[contains(@class, "el-button--primary")]')
    #         # locator = ('xpath', './/button[@class="el-button el-button--primary"]')
    #         confirm = Button(locator=locator, parent=self.ele)
    #         confirm.click()
    #         self.driver.wait_not_element(element=self.locator)
    #         time.sleep(1)

    def confirm(self, text="确定", wait=True):
        if self.is_exists is True:
            log.debug("*.click modal confirm.")
            # locator = ('xpath', './/button[contains(@class, "el-button--primary")]')
            locator = ('xpath', './/span[normalize-space(text())="%s"]/parent::button' % text)
            # locator = ('xpath', './/button[@class="el-button el-button--primary"]')
            # ::todo  临时修改
            # confirm = Button(text=text, parent=self.ele)
            confirm = Button(locator=locator, parent=self.ele)
            confirm.click()
            if wait:
                self.driver.wait_not_element(element=locator)
            time.sleep(1)


class ActionTips(Dialog):

    def __init__(self, parent=None):
        super(ActionTips, self).__init__(
            u"操作提示", parent)


class TabNavigator(Element):
    """详情页面，页签切换按钮"""
    def __init__(self, locator=None, parent=None):
        locator = locator or ('xpath', './/div[@role="tablist"]')
        super(TabNavigator, self).__init__(locator, parent)

    def switch_to(self, text):
        """切换Tab

        :param text: tab页签文本名称
        :return:
        """

        locator = ('xpath', './/div[text()="%s"]' % text)
        tab = Button(locator, parent=self.ele)
        if "is-active" in tab.attribute("class"):
            return
        else:
            tab.click()


class PanelView(Element):
    """详情页面: panel面板"""
    def __init__(self, locator, flag=None, parent=None):
        """详情页面板

        :param locator: panel定位方式
        :param flag:    panel等待信息加载完成的行标签文本
            如，flag=u"实例名称"
            会等待页面【实例名称】字段数据加载完成
        :param parent:
        """

        super(PanelView, self).__init__(locator, parent)
        self.wait_detail_info_loading(flag=flag)

    def trigger_create(self, text=None):
        """触发相应动作"""
        locator = ('xpath', './/button[text()=%s]' % text)
        self.driver.wait_element(element=locator, seconds=90)
        time.sleep(2)
        btn = Button(locator, parent=self.ele)
        btn.click()

    @staticmethod
    def get_flag(text):
        """标识数据加载完成的定位器

        :param text: 数据行的文本
        :return:
        """

        flag_path = './/label[contains(., "%s")]/ancestor::li/p' % text
        return 'xpath', flag_path

    def get_section_info(self, locator):
        """获取某个区域的详情信息

        :param locator: 定位到区域的定位方式，推荐定位到如下层级<ul>
            <div class="accordion-group" /div>
                <label class="accordion-heading" /div>
                <div class="accordion-body-xxx" /div>
                  <span class="accordion-inner" /ul>
                        ......
        :return:
        """

        section = Element(locator, parent=self.ele).ele
        rows = Elements(('class', "el-form-item"),
                        parent=section).ele
        info = dict()
        for row in rows:
            key = Element(('xpath', './label'), parent=row).ele.\
                text.replace("：", "")
            values = Elements(('xpath', './/span'), parent=row).texts()
            values = [val.strip() for val in values]
            values = list(filter(lambda x: any(x), values))
            value = None if not any(values) else (
                values[0] if len(values) == 1 else values)
            info.update({key: value})
        log.info(info)
        return info

    def wait_detail_info_loading(self, flag=None, time_out=120):
        """进入详情页面，等待数据tab标签加载数据

        :param flag:     panel view数据是否加载的行标签
        :param time_out: 超时时间
        :return:
        """

        if flag is None:
            return
        t_out = time.time() + time_out  # 超时设置
        locator = self.get_flag(flag)
        while time.time() < t_out:
            try:
                content = Element(locator, parent=self.ele).ele.text
            except Exception as e:
                log.debug(e)
                log.debug("Warning!!!The element is not appear yet!")
            else:
                if content is None:
                    continue
                content = str(content).strip()
                if len(content) > 0:
                    log.debug(content)
                    break


class OrderConfirm(Element):
    """订单确认页面基类"""
    def __init__(self, locator=None, parent=None):
        modal_xpath = './/div[@class="order_form"]'
        self.locator = locator or ('xpath', modal_xpath)
        super(OrderConfirm, self).__init__(self.locator, parent)

    def find_element(self):
        self.ele = self.driver.wait_element(
            element=self.locator, condition=Condition.visible)

    def confirm(self, text="提交订单"):
        log.debug("*.click modal confirm.")
        confirm = Button(text=text, parent=self.ele)
        confirm.click()
        time.sleep(1)


class LoginPage(object):
    """登录页面"""
    def __init__(self):
        self.driver = ActionBase()
        self.locator = ('class', 'content')
        self.login_timeout = 120

    def find_element(self):
        self.driver.wait_element(
            element=self.locator, condition=Condition.visible,
            seconds=60
        )

    def get_login(self):
        uri = getattr(CloudConf(), 'url')
        self.driver.get(uri)
    @retry_on_exception(tries=3, delay=1, backoff=2, max_delay=10)
    def login(self, username=None, password=None, verify_code=None):
        self.get_login()
        have_login = self.is_already_login()
        if have_login:
            # ignore login action if have already logged in
            log.info("already login, ignore login action!")
            return
        else:
            log.info("loginout,need cas login!")
            on_login_page = self.is_on_login_page()
            if not on_login_page:
                # not login and not on login page
                log.info("Warning!!!Not have login and not on login page.")
                body = Element(locator=('xpath', './*'))
                self.driver.get_screen_shot(element=body.ele)
                return
            else:
                # perform login, current status is logged out
                have_login or self.find_element()
                user = username or CloudConf().username
                pwd = password or CloudConf().password
                verify_code = verify_code or CloudConf().verify_code
                Button(('class', "user-login")).click()
                locator_user = ('id', 'username')
                log.info("log in with user: %s" % user)
                Input(locator_user).input(user)
                locator_pass = ('id', 'password')
                Input(locator_pass).input(pwd)
                Input(('id', 'verifyCode')).input(verify_code)
                Button(('class', 'login-button')).click()  #点击登录
                expire = time.time() + self.login_timeout
                already_login = False
                while time.time() < expire:
                    time.sleep(2)
                    already_login = self.is_already_login()
                    if already_login:
                        break

                if already_login:
                    cookies = self.driver.web_driver.get_cookies()
                    log.info("login with cookies=%s" % cookies)
                    log.info("登录成功!")
                else:
                    #TODO 登录失败重试 or token过期重试登录
                    try:
                        time.sleep(0.5)
                        have_login or self.find_element()
                        user = username or CloudConf().username
                        pwd = password or CloudConf().password
                        verify_code = verify_code or CloudConf().verify_code
                        Button(('class', "user-login")).click()
                        locator_user = ('id', 'username')
                        log.info("log in with user: %s" % user)
                        Input(locator_user).input(user)
                        locator_pass = ('id', 'password')
                        Input(locator_pass).input(pwd)
                        Input(('id', 'verifyCode')).input(verify_code)
                        Button(('class', 'login-button')).click()
                        log.info("retry login .")
                    except Exception as e:
                        log.error("Error login or token expired login error: %s" % e)
                        raise ValueError("登录失败")

    def do_logout(self):
        # logout(get exit href and get)
        gate = Button(locator=('xpath', './/div[@class="user-info"]//img'))
        gate.click()
        exit = Button(locator=('xpath',
                               ".//span[normalize-space(text())='退出登录']"))
        exit.click()
        time.sleep(0.8)

    def logout(self):
        # wait exit ready
        expire = time.time() + self.login_timeout
        already_login = False
        while time.time() < expire:
            time.sleep(2)
            already_login = self.is_already_login()
            if not already_login:
                break
            else:
                self.do_logout()

        if already_login:
            raise ValueError("Logout failed!")
        else:
            log.info("logout success!")

    def switch_tenant(self, tenant_name):
        log.error("tenantnane%s", tenant_name)
        Button(('class', "tenant-name")).click()
        # /html/body/div/div/div[1]/div/div/div/div[1]/div/div[4]/div[2]/section[3]/ul/li[4]/div[2]/button
        in_tenant = Button(locator=('xpath', "//span[@title='%s']/../../div[@class='enter-btn-area']/button[@type='button']" %tenant_name))
        in_tenant.click()

    @staticmethod
    def is_already_login():
        """是否已经登录"""
        locator = ('class', 'user-info')
        try:
            ActionBase().find_element(locator=locator)
            login = True
        except NoSuchElementException as e:
            log.debug(e)
            login = False
        return login

    def is_on_login_page(self):
        """是否在登录页"""
        try:
            ActionBase().wait_element(element=self.locator)
            login_page = True
        except NoSuchElementException as e:
            log.debug(e)
            login_page = False
        return login_page

