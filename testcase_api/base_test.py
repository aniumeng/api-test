#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import sys
import uuid
import logging
import os
import pytest, allure, json
import re
# from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont
from io import BytesIO
from common.utility import CloudConf
from common.utility import get_cur_path
import time
from nose.tools import eq_, assert_in
from common.rest_client import RestClient


log = logging.getLogger(__name__)


class BaseTest(object):
    """测试基类,setup_class和teardown_class子类不可改写
       setup_class会做2个动作，拿到登录认证，拿到微服务的client，可在子类重写

    """
    execute_from = None
    config = None
    struct_msg = None
    #env = os.getenv('env').lower()
    _outcome = None
    setup_cleanup_list = None

    # SYSTEM_CODE = getattr(CloudConf(), 'system_code')
    # REGION = getattr(CloudConf(), 'region')
    # ZONE = getattr(CloudConf(), 'zone')
    # VPC = getattr(CloudConf(), 'vpc')
    # CLUSTER = getattr(CloudConf(), 'cluster')
    # WARE_HOUSE = getattr(CloudConf(), 'ware_house')
    # PRIVATE_WARE_HOUSE = getattr(CloudConf(), 'private_ware_house')
    # IMAGE = getattr(CloudConf(), 'image_name')
    # NGINX_IMAGE = getattr(CloudConf(), 'nginx_image_name')
    # DUBBO_IMAGE = getattr(CloudConf(), 'dubbo_image_name')
    # DISASTER_ZONE = getattr(CloudConf(), 'disaster_zone')
    # PEAK_ZONE = getattr(CloudConf(), 'peak_zone')

    credential = None

    TIMEOUT_SCALING_FACTOR = 1

    @classmethod
    def setup_class(cls):
        BaseTest.json_data_shots = list()
        cls.setup_credentials()
        cls.setup_clients()
        cls.setup_resource()

    @classmethod
    def teardown_class(cls):
        log.info("Begin TeardownClass")
        try:
            cls.clean_resource()
        finally:
            log.info("EndFor TearDOWNCLASS")

    @classmethod
    def setup_credentials(cls):
        # auth_provider = RestClient().auth_providers
        # cls.credential = auth_provider
        pass

    @classmethod
    def setup_clients(cls):
        pass

    def setup(self):
        pass

    def teardown(self):
        pass
        # if self._outcome.errors:
        #     log.info("Save file response".center(50, "*"))
        #     response_file = self.json_data_shots[-1]
        #     # get last shot of fail
        #     allure.attach(json.dumps(response_file, ensure_ascii=False),
        #                   name="json_data",
        #                   attachment_type=allure.attachment_type.JSON)

    @classmethod
    def clean_resource(cls):
        log.info("Will clean resource")

    @classmethod
    def setup_resource(cls):
        log.info("Will setup test resource")

    @staticmethod
    def validator_common(expect_message, response_data, expect_result=1,
                         expect_success=True):
        message = response_data.get("message")
        result = response_data.get("result")
        success = response_data.get("success")
        allure.attach(json.dumps(response_data, ensure_ascii=False), name="json_data",
                      attachment_type=allure.attachment_type.JSON)
        assert_in(expect_message, message, msg="message返回：%s" % message)
        eq_(expect_result, result, msg="result返回值： %s" % result)
        eq_(expect_success, success, msg="success返回值：%s" % success)

    @staticmethod
    def expect_handle(valida_data, response_data):
        import jsonpath
        return jsonpath.jsonpath(response_data, valida_data)

    @staticmethod
    def validator_data(valida_data, comparator, expect, response_data):
        if valida_data.startswith('$.'):
            response_data = BaseTest.expect_handle(valida_data, response_data)[0]
        if comparator in ["eq", "equals", "==", "is", "="]:
            if expect is not None and (expect.startswith('int(') or expect.startswith('float(')):
                expect = eval(expect)
            assert str(expect) == str(response_data), "{} 期望 {}，实际为 {}".format(
                valida_data, expect, response_data)
        elif comparator in ["contains", "in"]:
            assert_in(expect, response_data,
                      msg="{} 期望包含 {}，实际为{}".format(valida_data, expect,
                                                  response_data))
        elif comparator in ["not", "!=", ]:
            assert response_data != expect, "{} 期望不为 {}，实际为{}".format(valida_data,
                                                                    expect,
                                                                    response_data)

    def validator_expect(self, expect, response_data):
        """断言

        :param expect:               断言表达式
        :param response_data:        返回的数据
        :return:
        """
        if expect:
            for ex in expect:
                valida_data, compare, expect = self.__parser_expect(ex)
                self.validator_data(valida_data, compare, expect, response_data)

    @staticmethod
    def __parser_expect(_expect):
        (valida_data, comparator, expect) = re.split(r'[^A-Za-z0-9$._\w() ]', _expect)
        if not comparator:
            comparator = "".join(re.split(r'[A-Za-z0-9$._\w()]', _expect))
        return valida_data, comparator, expect







