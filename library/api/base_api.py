#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import logging

from common.rest_client import RestClient
from common.utility import CloudConf

log = logging.getLogger(__name__)


def uri(add):
    def my_uri(func):
        def wrapper(self, *args, **kwargs):
            if not add.startswith("/"):
                url = self.font_page + "/" + add
            else:
                url = self.font_page + add
            self.url = url
            return func(self, *args, **kwargs)
        return wrapper
    return my_uri


class OrderApi(RestClient):

    # def __init__(self, auth_provider):
    #     super(P, self).__init__(auth_provider=auth_provider)
    #     header = {'page': 'portal', 'Host': self.font_page[7:]}
    #     self.s.headers.update(header)
    #     if auth_provider is not None:
    #         self.s.headers.update({'status': auth_provider})

    def __init__(self):
        super(OrderApi, self).__init__()
        self.url = None

    # def get_status(self):
    #     uri = "/permission-service/user/onlyUserDetail"
    #     header = {'page': 'portal', 'Host': self.font_page[7:]}
    #     self.http_ojb.headers.update(header)
    #     url = self.font_page + uri
    #     body = self.get(url=url)
    #     return body

    def get_status(self):
        uri = "/permission-service/user/userDetailForPlatform"
        header = {'page': 'portal', 'Host': self.font_page[7:]}
        self.http_ojb.headers.update(header)
        url = self.font_page + uri
        body = self.get(url=url)
        return body

    def find_system_code(self):
        uri = "/control-service/console-api/findSystemCodes"
        url = self.font_page + uri
        body = self.get(url)
        return body

    # @property
    # def console(self):
    #     return self.q.client


class TaskApi(RestClient):
    def __init__(self, auth_provider):
        super(TaskApi, self).__init__(auth_provider=auth_provider,
                                     endpoint_type='ops')
        self.url = None

    def get_status(self):
        uri = "/permission-service/user/onlyUserDetail"
        header = {'page': self.endpoint_type, 'Host': self.font_page[7:]}
        self.http_ojb.headers.update(header)
        url = self.font_page + uri
        body = self.get(url=url)
        if '成功获取用户信息但为空' in body.get('message'):
            tenant_dict = self.get_tenant()
            ops_role = getattr(CloudConf(), 'ops_role')
            if ops_role in tenant_dict.keys():
                self.switch_tenant(tenant_dict.get(ops_role))
            else:
                self.switch_tenant(tenant_dict.values()[0])
            body = self.get_user_detailForPlatform()
        return body

    def get_tenant(self):
        uri = '/permission-service/tenant/tenant'
        body = self.get(self.font_page + uri)
        tenant_dict = dict([(key.get('tenantName'), key.get('tenantKey')) for key in body.get('data')])
        return tenant_dict

    def switch_tenant(self, tenant):
        """选择角色"""
        uri = '/permission-service/tenant/switch/tenant/' + tenant
        self.get(self.font_page + uri)

    def get_user_detailForPlatform(self):
        uri = '/permission-service/user/userDetailForPlatform'
        body = self.get(self.font_page + uri)
        return body

    @property
    def console(self):
        return self.http_ojb



