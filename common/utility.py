#!/usr/bin/env python
# -*- coding: utf-8 -*-


import configparser
import logging
import os
import random
import copy
import time
import yaml

from selenium import webdriver
import sys
import string
from xlrd import open_workbook
from datetime import datetime
import requests
import re
import inspect
from requests.cookies import RequestsCookieJar
from _pytest.mark.structures import ParameterSet as ps
from _pytest.mark.structures import MarkDecorator
from _pytest.mark.structures import Mark


log = logging.getLogger(__name__)


def get_cur_path():
    # if is_windows():
    #     project_path = os.path.abspath(__file__.decode('gbk'))
    # else:
    project_path = os.path.abspath(__file__)
    project_path = os.path.dirname(project_path)
    return project_path


def is_windows():
    win = sys.platform.startswith("win")
    return win


def get_temp_path(filename=None):
    project_path = get_cur_path()
    res = os.path.join(project_path, "data", "temp")
    if filename is not None:
        res = os.path.join(res, filename)
    return res


def get_resource_name(res_type='', infix=None, size=None, endswith=None):
    """
    生成资源随机名字

    :param res_type:   前缀
    :param infix:      连接线
    :param size:       大小限制
    :param endswith:   以什么结尾 str
    :return:  前缀时间格式
    """
    dt = datetime.now()
    if infix is None:
        stamp = dt.strftime('%m%d-%H%M%f')
    else:
        stamp = dt.strftime('%m%d' + infix + '%H%M%f')
    name = res_type + stamp
    if isinstance(size, int):
        name = name[:size]
    if endswith is not None and type(endswith()) == str:
        name = name + random.choice(string.ascii_lowercase)
    starts = getattr(CloudConf(), 'starts')
    if starts:
       name = starts + name
    return name


class ConfigBase(object):

    def __init__(self, cfg_file=None, need_read_part=False):
        self.config = configparser.ConfigParser()
        self.config.read(cfg_file, encoding="utf-8")
        self.cfg_ = dict()
        if os.getenv("env") == "sit" and need_read_part:
            self.__read_part("Base")
            self.__read_part(os.getenv("tenant"))
        else:
            self.__read_all()

    def __read_all(self):
        sections = self.config.sections()
        for section in sections:
            options = self.config.options(section)
            for option in options:
                self.cfg_.update(
                    {option: self.config.get(section, option)})

    def __read_part(self, tenant):
        options = self.config.options(tenant)
        for option in options:
            self.cfg_.update(
                {option: self.config.get(tenant, option)})

    @property
    def cfg(self):
        return self.cfg_


class CloudConf(object):
    INSTANCE = None
    INITIALIZED = False

    def __new__(cls, *args, **kwargs):
        if cls.INSTANCE is None:
            cls.INSTANCE = super(CloudConf, cls).__new__(cls)
        return cls.INSTANCE

    def __init__(self):
        if self.INITIALIZED is False:
            # self.username = None
            # self.password = None
            # self.verify_code = None
            self.url = "http://127.0.0.1:9091"
            # self.ops_url = None
            # self.base_cfg = base_cfg
            # #self.user_cfg = user_cfg
            # self.cfg_ = None
            # self.__get_config_file()
            # self.__build_config()
            # self.__set_attribute()
            self.INITIALIZED = True

    # def __get_config_file(self):
    #     if self.base_cfg is None:
    #         self.base_cfg = os.path.join(
    #             get_cur_path(), '..\\conf', 'env_conf.yaml')
    #         with open(file=self.base_cfg, mode="r", encoding='utf-8') as f:
    #             self.url = yaml.safe_load(f).get('url')
        # if os.getenv("env").lower() not in ["ci", "sit"]:
        #     raise ValueError("Input env:%s Wrong!!!" % os.getenv("env"))
        # if self.user_cfg is None and os.getenv("env").lower() == 'ci':
        #     self.user_cfg = os.path.join(
        #         get_cur_path(), 'conf', 'ci_conf.yaml')
        # elif self.user_cfg is None and os.getenv("env").lower() == 'sit':
        #     self.user_cfg = os.path.join(
        #         get_cur_path(), 'conf', 'sit_conf.yaml')
        # else:
        #     self.user_cfg = os.path.join(
        #         get_cur_path(), 'conf', 'env_conf.yaml')

    def __build_config(self):
        base = ConfigBase(self.base_cfg).cfg
        user = ConfigBase(self.user_cfg, need_read_part=True).cfg
        self.cfg_ = base
        # self.cfg_ = user
        self.cfg_.update(user)

    def __set_attribute(self):
        for key in self.cfg_:
            setattr(self, key, self.cfg_.get(key))


class WebDriverManager(object):
    __INSTANCE__ = None
    __INITIALIZED__ = False

    def __new__(cls, *args, **kwargs):
        if cls.__INSTANCE__ is None:
            cls.__INSTANCE__ = super(
                WebDriverManager, cls).__new__(cls)
        return cls.__INSTANCE__

    @classmethod
    def release(cls):
        cls.__INSTANCE__ = None
        cls.__INITIALIZED__ = False

    def __init__(self, browser='Chrome'):
        if self.__INITIALIZED__ is True:
            return
        self.browser = browser.capitalize()
        log.debug(u"创建文件下载路径")
        download_path = get_temp_path()
        if not os.path.exists(download_path):
            os.mkdir(download_path)
        user_agent = 'user-agent=Mozilla/5.0 (X11; Linux x86_64' \
                     ') AppleWebKit/537.36 (KHTML, like Gecko' \
                     ') Chrome/72.0.3626.121 Safari/537.36'

        if self.browser == 'Firefox':
            # set profile
            profile = webdriver.FirefoxProfile()
            profile.set_preference("browser.download.folderList", 2)
            profile.set_preference("intl.accept_languages", "zh-cn")
            profile.set_preference(
                "browser.download.manager.showWhenStarting", False)
            profile.set_preference("browser.download.dir",
                                   download_path)
            profile.set_preference(
                "browser.helperApps.neverAsk.saveToDisk",
                "application/binary,application/vnd.ms-excel,"
                "application/x-msexcel,application/excel,"
                "application/x-excel,application/octet-stream,"
                "text/csv/xls,application/zip,application/x-gtar")
            # set options
            if getattr(CloudConf(), 'headless') == 'enabled':
                options = webdriver.FirefoxOptions()
                options.headless = True
                options.add_argument(user_agent)
            else:
                options = None
            # start browser
            self.web_driver_ = webdriver.Firefox(
                firefox_profile=profile, firefox_options=options
            )
        elif self.browser == "Chrome":
            # set options
            options = webdriver.ChromeOptions()
            # 浏览器内部命令模拟F12
            # options.add_argument("--auto-open-devtools-for-tabs")
            if getattr(CloudConf(), 'headless') == 'enabled':
                options.add_argument('headless')
                options.add_argument('no-sandbox')
                options.add_argument('disable-gpu')
                options.add_argument('window-size=1920x1080')
                options.add_argument(user_agent)

            prefs = {'profile.default_content_settings.popups': 0,
                     "download.default_directory": download_path}
            options.add_experimental_option("prefs", prefs)

            # start browser
            self.web_driver_ = webdriver.Chrome(
                options=options)

            # add missing support for chrome "send_command" to web_driver
            # @ref: https://stackoverflow.com/questions/45631715/
            # downloading-with-chrome-headless-and-selenium
            if getattr(CloudConf(), 'headless') == 'enabled':
                self.web_driver.command_executor._commands["send_command"] = (
                    "POST", '/session/$sessionId/chromium/send_command')
                params = {'cmd': 'Page.setDownloadBehavior',
                          'params': {'behavior': 'allow',
                                     'downloadPath': download_path}}
                command_result = self.web_driver_.execute(
                    "send_command", params)
                log.info("response from browser: %s", command_result)
                if command_result is None:
                    try:
                        time.sleep(0.5)
                        self.web_driver.command_executor._commands["send_command"] = (
                        "POST", '/session/$sessionId/chromium/send_command')
                    except Exception as e:
                        log.info("cmd result: %s" %e)
                else:
                    for key in command_result:
                        log.info("result:" + key + ":" + str(command_result[key]))
        else:
            raise ValueError(u"Support browser constrains in Firefox/Chrome!")
        self.maximize()
        self.__INITIALIZED__ = True

    @property
    def web_driver(self):
        return self.web_driver_

    def get(self, url):
        self.web_driver.get(url)

    def maximize(self):
        self.web_driver.maximize_window()

    def quit(self):
        self.web_driver.quit()

    def get_screen_shot(self):
        self.web_driver.get_screenshot_as_png()

    @property
    def url(self):
        return self.web_driver.current_url


class Excel(object):
    """参数化 测试，Excel数据处理模块"""
    CASE_NAME = 'case_name'
    USER_ROLE = 'user_role'
    EXPECT = 'expect'

    def __init__(self, sheet, excel):
        """

        :param sheet: 工作表名称
        :param excel: excel 文件名
        :param path:  路劲
        :return:
        """
        self.sheet = sheet
        self.excel = excel
        self.sheet_data = list()  # 原始数据
        self.iter_data = list()   # 处理后的行数据
        self.__get_sheet_data()
        self.__get_param_data()

    @property
    def row_list(self):
        """处理后的数据

        说明：结构如下
        [{'param1': xxx,
          'param2': xxx,
          'expect': {},
          'case_name': '',
          'u_role': '',
          },
          ...
        ]
        """
        return self.iter_data

    def __get_sheet_data(self):
        """获取数据表的原始数据，存入列表"""
        frame = inspect.stack()[2]
        filename = frame[0].f_code.co_filename
        file_path = os.path.dirname(filename)
        abs_path = os.path.join(
            file_path, 'data', self.excel + '.xlsx')
        # log.info("get excel file %s" % abs_path)
        book = open_workbook(abs_path)
        sheet = book.sheet_by_name(self.sheet)
        # get one sheet's rows
        n_rows = sheet.nrows
        for i in range(n_rows):
            if sheet.row_values(i)[0] != u'case_id':
                new_list = [x if x else None for x in sheet.row_values(i)[1:]]
                self.sheet_data.append(dict(
                    zip(sheet.row_values(0)[1:], new_list)))

    @staticmethod
    def is_able_eval(val):
        """解析列参数"""
        if val.startswith('int(') and val.endswith(')'):
            able = True  # 整型
        elif val.startswith('float(') and val.endswith(')'):
            able = True  # 浮点型
        elif val.startswith('bool(') and val.endswith(')'):
            able = True  # 布尔型
        elif val.startswith('list(') and val.endswith(')'):
            able = True  # 列表型
        elif val.startswith('dict(') and val.endswith(')'):
            able = True  # 字典型
        elif val.startswith('{') and val.endswith('}'):
            able = False  # json
        elif val.startswith('file(') and val.endswith(')'):
            able = True
        elif val == 'None':
            able = True  # None型
        else:
            able = False
        return able

    def __parse_row_param(self, row_dict):
        """解析行参数"""
        row = dict()
        for col_k, col_v in row_dict.items():
            if col_v is None or len(col_v) == 0:
                continue
            elif self.is_able_eval(col_v):
                col_v = eval(col_v)
            else:
                pass
            row.update({col_k: col_v})
        return row

    def __get_param_data(self):
        """有效参数"""
        for row_data in self.sheet_data:
            row = dict()
            row_dict = copy.deepcopy(row_data)
            expect = row_dict.pop(self.EXPECT)
            expect_list = expect.split(',') if expect else []
            case_name = row_dict.pop(self.CASE_NAME)
            row.update(expect=expect_list)
            row.update(self.__parse_row_param(row_dict))
            mark_de = self.__parser_mark(row.get("level"))
            ddd = ps._make([[row], [mark_de], case_name])
            self.iter_data.append(ddd)

    @staticmethod
    def __parser_mark(marker):
        """excel标签处理"""
        if marker is None:
            return
        mark = Mark(name=marker, args=(), kwargs={})
        mark_de = MarkDecorator(mark=mark)
        return mark_de
