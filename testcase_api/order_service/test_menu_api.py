#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from testcase_api.base_test import BaseTest
from common.utility import Excel
from common.utility import CloudConf
from library.api.portal.order_service.menu_client import MenuClient
import pytest
import logging, time
import allure
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)


class TestMenuApi(BaseTest):

    @classmethod
    def setup_clients(cls):
        cls.menu = MenuClient()

    @classmethod
    def setup_resource(cls):
        cls.userName = "user01"
        cls.password = "pwd"
        cls.order_list = [
                {
                    "menu_nember": "01",
                    "number": 1
                },
                {
                    "menu_number": "03",
                    "number": 3
                }
            ]

    def _order_validator_common(self, response):
        self.validator_common("请求成功", response)

    def _order_validator_data_not_none(self, response):
        self.validator_data("$.data", '!in', ["", [], None], response)

    def _order_validator_data_is_none(self, response):
        self.validator_data("$.data", '==', None, response)


@allure.suite('菜单接口测试')
class TestMockApi(TestMenuApi):
    """mock_api"""

    @classmethod
    def setup_resource(cls):
        super(TestMockApi, cls).setup_resource()


    #@pytest.mark.parametrize
    def test_user_login(self):
        """用户登录 /api/v1/user/login"""
        response = self.menu.user_login(json={'authRequest': {'userName': self.userName,'password': self.password}})
        token = response.get('access_token')
        # self.validator_common(expect_message="请求成功", expect_success=True,
        #                       expect_result=None, response_data=response)
        #self._order_validator_data_not_none(response)
        print(response)
        print(token)
        return token

    def test_see_menu_list(self):
        """查看菜单 /api/v1/menu/list"""
        # TestMockApi().test_user_login()
        headers = {
            "access_token": "3b6754f00bb0063071c5b71ce2b56b4ed0ce56a63493e785bea85b74c41ce200",
            "Content-Type": "application/json"
        }
        response = self.menu.see_menu_list(headers=headers)
        print(response)
        # self.validator_common(expect_message="", response_data=response)
        #self._order_validator_data_not_none(response)


    def test_conform_menu(self):
        """确认菜单 /api/v1/menu/confirm"""
        headers = {
            'access_token': TestMockApi().test_user_login(),
            'Content-Type': 'application/json'
        }
        response = self.menu.conform_menu(self.order_list,headers=headers)
        print(response)

        # self.validator_common(expect_message="", response_data=response)
        #self._order_validator_data_not_none(response)

    def test_user_logout(self):
        """用户退出登录 /api/v1/user/logout"""
        headers = {
            'access_token': TestMockApi().test_user_login(),
            'Content-Type': 'application/json'
        }
        response = self.menu.user_logout(headers=headers)
        print(response)
        # self.validator_common(expect_message="", response_data=response)
        #self._order_validator_data_not_none(response)

