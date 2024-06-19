#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
from library.api.base_api import OrderApi
from library.api.base_api import uri

import os

class Schema:

    SCHEMA_DATA_MSG_SUCCESS_CODE = {
        "type": "object",
        "properties": {
            'data': {
                "type": ["null", "object", "string", "array", "number"],
            },
            'message': {
                "description": "response message",
                "type": ["string", "number"],
            },
            'success': {
                "description": "response success or not",
                "type": 'boolean',
            },
            'code': {
                "description": "response code",
                "type": 'number',
            }
        },
        "required": ['data', 'message', 'success', 'code']
    }


class MenuClient(OrderApi):

    @uri("/api/v1/user/login")
    def user_login(self, json):
        """用户登录

        :return:
        """
        body = self.post(url=self.url, json=json)
        return body

    @uri("/api/v1/menu/list")
    def see_menu_list(self):
        """查看菜单

        :return:
        """
        body = self.get(url=self.url)
        return body

    @uri("/api/v1/menu/confirm")
    def conform_menu(self, order_list):
        """确认菜单

        :return:
        """

        body = self.post(url=self.url, json={'order_list': order_list})
        return body

    @uri("/api/v1/user/logout")
    def user_logout(self):
        """用户退出登录
        access_token
        :return:
        """
        body = self.delete(url=self.url)
        return body
