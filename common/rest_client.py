
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import requests
from common.utility import CloudConf
from requests.cookies import RequestsCookieJar
from pprint import pformat
import jsonschema
import json

log = logging.getLogger(__name__)

HTTP_SUCCESS = (200, 201, 202, 203, 204, 205, 206, 207)

HTTP_REDIRECTION = (300, 301, 302, 303, 304, 305, 306, 307)
JSONSCHEMA_VALIDATOR = jsonschema.Draft3Validator
FORMAT_CHECKER = jsonschema.draft3_format_checker

LOG = logging.getLogger(__name__)


def retry(func):
    def wrapper(self, *args, **kwargs):
        ur = func(self, *args, **kwargs)
        if ur == "" or ur is None:
            return ur
        elif ur.get('code') == 'reloading' and 'status had changed' \
                in ur.get('code_message'):
            LOG.info("status has changed, update again!!!!")
            self.update_header()
            return func(self, *args, **kwargs)
        elif ur.get('code_message') == ' Token was not recognised':
            LOG.info("认证失败")
            assert False, "认证失败%s" % ur
        elif ur.get('code_message') == ' no login':
            LOG.info('登录失败')
            assert False, "登录失败%s" % ur
        # elif u.get('code') == 'reloading' and 'Token was not recognised' \
        #         in u.get('code_message'):
        #     LOG.info("Login again!!!")
        #     self.app_verify()
        #     self.update_header()
        #     return func(self, *args, **kwargs)
        else:
            # assert False, "认证失败%s" % ur.get('data')
            return ur
    return wrapper


class RestClient(object):

    def __init__(self,http_timeout=60):
        # self.auth_provider = auth_provider
        self.font_page = getattr(CloudConf(), 'url')
        self.http_timeout = http_timeout
        self.http_ojb = requests.Session()
        self.jar = RequestsCookieJar()
        # if self.auth_provider is None:
        #     self.auth_provider = dict()
        #     self.app_verify() ## 真正登录
        #     self.update_header()
        # else:
        #    self.http_ojb.cookies = self.auth_provider.get('cookies')
        # self.update_header()


    @staticmethod
    def get_headers(accept_type=None, send_type=None):
        if accept_type is None:
            accept_type = 'json'
        if send_type is None:
            send_type = 'json'
        headers = {'Content-Type': 'application/%s' % send_type,
                   'Accept': 'application/%s' % accept_type}
        # headers.update(profiler.serialize_as_http_headers())
        return headers

    # def app_verify(self):
    #     """app授权"""
    #     cas_url = self._get_page_id()
    #     lt, iddd = self._get_lt(cas_url)
    #     self._login(cas_url, lt, iddd, username=self.username,
    #                 password=self.password)
    #     # self.http_ojb.get(url=self.font_page)
    #     """
    #     self.get(url=self.font_page)
    #     self.http_ojb.headers.update(self.get_data_headers())
    #     status = self.get_status()
    #     self.auth_status = status.get("data").get("status")
    #     self.http_ojb.headers.update({'status': self.auth_status})
    #     """
    #     # self.auth_provider.status = self.auth_status

    # def update_header(self):
    #     #
    #     # cookies = requests.utils.cookiejar_from_dict(cookies_dict,
    #     #                                              cookiejar=None,
    #     #                                              overwrite=True)
    #     # self.http_ojb.cookies = cookies
    #     # self.http_ojb.headers.update(self.auth_provider)
    #     self.update_status()
    #     self.http_ojb.headers.update({'validateBackPass': 'true'})
    #     self.http_ojb.headers.update({'status': self.auth_provider.get('status')})

    def get_data_headers(self):
        headers = {
            "Accept": "application/json, text/plain, */*",
        }
        return headers

    # def update_header(self):
    #     st = self.get_status()
    #     auth_status = st.get("data").get("status")
    #     self.http_ojb.headers.update(
    #         {'status': auth_status})

    # def get_status(self):
    #     uri = "/permission-service/user/onlyUserDetail"
    #     header = {'page': 'portal', 'Host': self.font_page[7:]}
    #     self.http_ojb.headers.update(header)
    #     url = self.font_page + uri
    #     body = self.get(url=url)
    #     return body

    def get_cookies(self):
        cookie_dict = requests.utils.dict_from_cookiejar(self.http_ojb.cookies)
        cookies = requests.utils.cookiejar_from_dict(cookie_dict,
                                                     cookiejar=None,
                                                     overwrite=True)
        self.auth_provider['cookies'] = cookies

    # def update_status(self):
    #     st = self.get_status()
    #     auth_status = st.get("data").get("status")
    #     self.auth_provider['status'] = auth_status

    # @property
    # def auth_providers(self):
    #     self.get_cookies()
    #     self.update_status()
    #     return self.auth_provider

    # def _get_page_id(self):
    #     body = self.get(url=self.font_page +
    #                     '/permission-service/login?page=&type=portal')
    #     return body.get('data')

    # def _get_lt(self, url):
    #     body = self.http_ojb.get(url=url)
    #     # body = self.get(url=url)
    #     import re
    #     lt = re.findall('name="lt" value="(.*)"', body.text)
    #     iddds = re.findall('name="iddds" value="(.*)"', body.text)
    #     return lt[0], iddds[0]
    #
    # def _login(self, url, lt, iddds, username, password):
    #     log.info("log in %s password %s" % (username, password))
    #     data = {
    #         'lt': lt,
    #         '_eventId': 'submit',
    #         'qrcodeId': None,
    #         'iddds': iddds,
    #         'username': username,
    #         'password': password,
    #         "verifyCode": '123'
    #     }
    #     self.http_ojb.post(url, data=data, verify=False)
    #     # self.post(url, data=data)
    #
    # def get_arrangement(self, name=""):
    #     uri = '/biz_service/arrange/getArrangeDataNew'
    #     _json = {'currentPage': 1, 'name': name, 'pageSize': 10,
    #              'status': "", 'vendorId': ""}
    #     url = self.font_page + uri
    #     body = self.post(url=url, json=_json)
    #     return body

    @retry
    def get(self, url, check=True, schema=None, **kwargs):
        log.info("Requests get URL is %s" % url)
        abs_url = url
        if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
            kwargs = str(kwargs).replace("json", "params")
            kwargs = eval(kwargs)
        if kwargs is not None:
            abs_url = abs_url.format(**kwargs)
        rsp = self.http_ojb.get(url=abs_url, timeout=self.http_timeout,
                                params=kwargs.get("params"))
        return self.__serialize_response(rsp, check, schema)

    @retry
    def post(self, url, check=True, schema=None, **kwargs):
        log.info("Requests post URL is %s" % url)
        log.debug("url %s params is %s " % (url, pformat(kwargs.get('json'))))
        abs_url = url
        if kwargs is not None:
            abs_url = abs_url.format(**kwargs)
        if 'file' in kwargs:
            rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
                                     files={'file': kwargs.get('file')})
        elif 'params' in kwargs or 'json' in kwargs:
            rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
                                     params=kwargs.get('params'), json=kwargs.get('json'))
        else:
            rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
                                     json=kwargs.get('json'))
        # return rsp.status_code, self.__serialize_response(rsp)
        # return rsp.status_code, rsp.content
        return self.__serialize_response(rsp, check, schema)

    @retry
    def patch(self, url, schema=None, **kwargs):
        log.info("Requests patch Url is %s" % url)
        abs_url = url
        if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
            kwargs = str(kwargs).replace("json", "params")
            kwargs = eval(kwargs)
        if kwargs is not None:
            abs_url = abs_url.format(**kwargs)
        rsp = self.http_ojb.patch(url=abs_url, timeout=self.http_timeout,
                                  params=kwargs.get("params"))
        return self.__serialize_response(rsp, schema)

    @retry
    def put(self, url, check=True, schema=None, **kwargs):
        log.info("Requests patch Url is %s" % url)
        abs_url = url
        if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
            kwargs = str(kwargs).replace("json", "params")
            kwargs = eval(kwargs)
        if kwargs is not None:
            abs_url = abs_url.format(**kwargs)
        rsp = self.http_ojb.put(url=abs_url, timeout=self.http_timeout,
                                  json=kwargs.get("params"))
        return self.__serialize_response(rsp, check, schema)

    @retry
    def delete(self, url, **kwargs):
        log.info("Requests delete URL is %s" % url)
        abs_url = url
        if kwargs is not None:
            abs_url = abs_url.format(**kwargs)
        rsp = self.http_ojb.delete(url=abs_url, timeout=self.http_timeout, json=kwargs.get('json'))
        return self.__serialize_response(rsp)

    def __serialize_response(self, response, check=True, schema=None):
        response.raise_for_status()
        log.info("%s 响应时长为: %s 秒" % (response.url,
                                     response.elapsed.total_seconds()))
        content = response.text
        if check is False:
            return ""
        if content == '' or '[]' == response.text or 'stream' in response.headers.get('Content-Type'):
            rsp_body = None
        else:
            try:
                rsp_body = response.json()
                log.debug(rsp_body)
                schema = schema or self.schema or self.redirect_schema
                self.validate_response(schema=schema, body=rsp_body)
            except Exception as e:
                assert 'Failed validating' not in str(e), e
                log.info(e)
                log.info(e)
                if 'status had changed' in str(
                        e) or 'Token was not recognised' in str(e) or 'no login' in str(e):
                    pass
                else:
                    assert '返回模式匹配失败' not in str(e), e
                rsp_body = response.json()
        log.debug("响应内容为{}".format(pformat(rsp_body)))
        return rsp_body

    @classmethod
    def expected_success(cls, expected_code, read_code):
        if not isinstance(read_code, int):
            raise TypeError("'read_code' must be an int instead of (%s)"
                            % type(read_code))

        assert_msg = ("This function only allowed to use for HTTP status "
                      "codes which explicitly defined in the RFC 7231 & 4918. "
                      "{0} is not a defined Success Code!"
                      ).format(expected_code)
        if isinstance(expected_code, list):
            for code in expected_code:
                assert code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg
        else:
            assert expected_code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg

        if read_code < 400:
            pattern = ("Unexpected http success status code {0}, "
                       "The expected status code is {1}")
            if ((not isinstance(expected_code, list) and
                 (read_code != expected_code)) or
                    (isinstance(expected_code, list) and
                     (read_code not in expected_code))):
                details = pattern.format(read_code, expected_code)
                raise requests.exceptions.InvalidSchema(details)

    @classmethod
    def validate_response(cls, schema, body):
        """ 模式匹配校验

        :param schema:  schema模式
        :param body:    校验的内容
        :return:
        """
        if schema:
            if isinstance(schema, str):
                schema = json.loads(schema)
            try:
                # jsonschema.validate(body, schema,
                #                     cls=JSONSCHEMA_VALIDATOR,
                #                     format_checker=FORMAT_CHECKER)
                jsonschema.validate(body, schema)
            except jsonschema.ValidationError as ex:
                msg = ("返回模式匹配失败，错误原因 %s 返回的是 %s" % (ex.message, ex.instance))

                raise requests.exceptions.HTTPError(msg)
        else:
            if body:
                msg = ("HTTP response body should not exist (%s)" % body)
                raise requests.exceptions.HTTPError(msg)


class ResponseBody(dict):
    """Class that wraps an http response and dict body into a single value.

    Callers that receive this object will normally use it as a dict but
    can extract the response if needed.
    """

    def __init__(self, response, body=None):
        body_data = body or {}
        self.update(body_data)
        self.response = response

    def __str__(self):
        body = super(ResponseBody, self).__str__()
        return "response: %s\nBody: %s" % (self.response, body)

# todo websocket
class WebSocket(object):
    schema = {
        "type": "object",
        "properties": {
            'data': {
                "type": ["null", "object", "string", "array", "number"],
            },
            'message': {
                "description": "response message",
                "type": "string",
            },
            'success': {
                "description": "response code",
                "type": 'boolean',
            },
            'result': {
                "description": "response result",
                "type": "number",
            }
        },
        "required": ['data', 'message', 'success', 'result']
    }

    def __init__(self, auth_provider=None, username=None, password=None,
                 url=None,
                 endpoint_type='portal',
                 http_timeout=60):
        self.auth_provider = auth_provider
        self.username = username or getattr(CloudConf(), 'username')
        self.password = password or getattr(CloudConf(), 'password')
        if endpoint_type == 'portal' and url is None:
            self.font_page = getattr(CloudConf(), 'url')
        elif endpoint_type == 'ops' and url is None:
            self.font_page = getattr(CloudConf(), 'ops_url')
        else:
            self.font_page = url
        self.endpoint_type = endpoint_type
        self.http_timeout = http_timeout
        self.http_ojb = requests.Session()
        self.jar = RequestsCookieJar()
        if self.auth_provider is None:
            self.auth_provider = dict()
            self.app_verify()
            self.update_header()
        else:
            self.http_ojb.cookies = self.auth_provider.get('cookies')
            self.update_header()

    @staticmethod
    def get_headers(accept_type=None, send_type=None):
        if accept_type is None:
            accept_type = 'json'
        if send_type is None:
            send_type = 'json'
        headers = {'Content-Type': 'application/%s' % send_type,
                   'Accept': 'application/%s' % accept_type}
        # headers.update(profiler.serialize_as_http_headers())
        return headers

    def app_verify(self):
        """app授权"""
        cas_url = self._get_page_id()
        lt, iddd = self._get_lt(cas_url)
        self._login(cas_url, lt, iddd, username=self.username,
                    password=self.password)
        # self.http_ojb.get(url=self.font_page)
        """
        self.get(url=self.font_page)
        self.http_ojb.headers.update(self.get_data_headers())
        status = self.get_status()
        self.auth_status = status.get("data").get("status")
        self.http_ojb.headers.update({'status': self.auth_status})
        """
        # self.auth_provider.status = self.auth_status

    def update_header(self):
        #
        # cookies = requests.utils.cookiejar_from_dict(cookies_dict,
        #                                              cookiejar=None,
        #                                              overwrite=True)
        # self.http_ojb.cookies = cookies
        # self.http_ojb.headers.update(self.auth_provider)
        self.update_status()
        self.http_ojb.headers.update({'validateBackPass': 'true'})
        self.http_ojb.headers.update({'status': self.auth_provider.get('status')})

    def get_data_headers(self):
        headers = {
            "Accept": "application/json, text/plain, */*",
        }
        return headers

    # def update_header(self):
    #     st = self.get_status()
    #     auth_status = st.get("data").get("status")
    #     self.http_ojb.headers.update(
    #         {'status': auth_status})

    def get_status(self):
        uri = "/permission-service/user/onlyUserDetail"
        header = {'page': 'portal', 'Host': self.font_page[7:]}
        self.http_ojb.headers.update(header)
        url = self.font_page + uri
        body = self.get(url=url)
        return body

    def get_cookies(self):
        cookie_dict = requests.utils.dict_from_cookiejar(self.http_ojb.cookies)
        cookies = requests.utils.cookiejar_from_dict(cookie_dict,
                                                     cookiejar=None,
                                                     overwrite=True)
        self.auth_provider['cookies'] = cookies

    def update_status(self):
        st = self.get_status()
        auth_status = st.get("data").get("status")
        self.auth_provider['status'] = auth_status

    @property
    def auth_providers(self):
        self.get_cookies()
        self.update_status()
        return self.auth_provider

    def _get_page_id(self):
        body = self.get(url=self.font_page +
                            '/permission-service/login?page=&type=')
        return body.get('data')

    def _get_lt(self, url):
        body = self.http_ojb.get(url=url)
        # body = self.get(url=url)
        import re
        lt = re.findall('name="lt" value="(.*)"', body.text)
        iddds = re.findall('name="iddds" value="(.*)"', body.text)
        return lt[0], iddds[0]

    def _login(self, url, lt, iddds, username, password):
        log.info("log in %s password %s" % (username, password))
        data = {
            'lt': lt,
            '_eventId': 'submit',
            'qrcodeId': None,
            'iddds': iddds,
            'username': username,
            'password': password,
            "verifyCode": '123'
        }
        self.http_ojb.post(url, data=data)
        # self.post(url, data=data)

    # def get_arrangement(self, name=""):
    #     uri = '/biz_service/arrange/getArrangeDataNew'
    #     _json = {'currentPage': 1, 'name': name, 'pageSize': 10,
    #              'status': "", 'vendorId': ""}
    #     url = self.font_page + uri
    #     body = self.post(url=url, json=_json)
    #     return body

    # @retry
    # def get(self, url, check=True, schema=None, **kwargs):
    #     log.info("Requests get URL is %s" % url)
    #     abs_url = url
    #     if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
    #         kwargs = str(kwargs).replace("json", "params")
    #         kwargs = eval(kwargs)
    #     if kwargs is not None:
    #         abs_url = abs_url.format(**kwargs)
    #     rsp = self.http_ojb.get(url=abs_url, timeout=self.http_timeout,
    #                             params=kwargs.get("params"))
    #     return self.__serialize_response(rsp, check, schema)
    #
    # @retry
    # def post(self, url, check=True, schema=None, **kwargs):
    #     log.info("Requests post URL is %s" % url)
    #     log.debug("url %s params is %s " % (url, pformat(kwargs.get('json'))))
    #     abs_url = url
    #     if kwargs is not None:
    #         abs_url = abs_url.format(**kwargs)
    #     if 'file' in kwargs:
    #         rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
    #                                  files={'file': kwargs.get('file')})
    #     elif 'params' in kwargs or 'json' in kwargs:
    #         rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
    #                                  params=kwargs.get('params'), json=kwargs.get('json'))
    #     else:
    #         rsp = self.http_ojb.post(url=abs_url, timeout=self.http_timeout,
    #                                  json=kwargs.get('json'))
    #     # return rsp.status_code, self.__serialize_response(rsp)
    #     # return rsp.status_code, rsp.content
    #     return self.__serialize_response(rsp, check, schema)
    #
    # @retry
    # def patch(self, url, schema=None, **kwargs):
    #     log.info("Requests patch Url is %s" % url)
    #     abs_url = url
    #     if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
    #         kwargs = str(kwargs).replace("json", "params")
    #         kwargs = eval(kwargs)
    #     if kwargs is not None:
    #         abs_url = abs_url.format(**kwargs)
    #     rsp = self.http_ojb.patch(url=abs_url, timeout=self.http_timeout,
    #                               params=kwargs.get("params"))
    #     return self.__serialize_response(rsp, schema)
    #
    # @retry
    # def put(self, url, check=True, schema=None, **kwargs):
    #     log.info("Requests patch Url is %s" % url)
    #     abs_url = url
    #     if kwargs is not None and isinstance(kwargs, dict) and 'json' in kwargs:
    #         kwargs = str(kwargs).replace("json", "params")
    #         kwargs = eval(kwargs)
    #     if kwargs is not None:
    #         abs_url = abs_url.format(**kwargs)
    #     rsp = self.http_ojb.put(url=abs_url, timeout=self.http_timeout,
    #                             json=kwargs.get("params"))
    #     return self.__serialize_response(rsp, check, schema)
    #
    # @retry
    # def delete(self, url, **kwargs):
    #     log.info("Requests delete URL is %s" % url)
    #     abs_url = url
    #     if kwargs is not None:
    #         abs_url = abs_url.format(**kwargs)
    #     rsp = self.http_ojb.delete(url=abs_url, timeout=self.http_timeout, json=kwargs.get('json'))
    #     return self.__serialize_response(rsp)

    def __serialize_response(self, response, check=True, schema=None):
        response.raise_for_status()
        log.info("%s 响应时长为: %s 秒" % (response.url,
                                     response.elapsed.total_seconds()))
        content = response.text
        if check is False:
            return ""
        if content == '' or '[]' == response.text or 'stream' in response.headers.get('Content-Type'):
            rsp_body = None
        else:
            try:
                rsp_body = response.json()
                log.debug(rsp_body)
                schema = schema or self.schema
                self.validate_response(schema=schema, body=rsp_body)
            except Exception as e:
                assert 'Failed validating' not in str(e), e
                log.info(e)
                log.info(e)
                if 'status had changed' in str(
                        e) or 'Token was not recognised' in str(e) or 'no login' in str(e):
                    pass
                else:
                    assert '返回模式匹配失败' not in str(e), e
                rsp_body = response.json()
        log.debug("响应内容为{}".format(pformat(rsp_body)))
        return rsp_body

    @classmethod
    def expected_success(cls, expected_code, read_code):
        if not isinstance(read_code, int):
            raise TypeError("'read_code' must be an int instead of (%s)"
                            % type(read_code))

        assert_msg = ("This function only allowed to use for HTTP status "
                      "codes which explicitly defined in the RFC 7231 & 4918. "
                      "{0} is not a defined Success Code!"
                      ).format(expected_code)
        if isinstance(expected_code, list):
            for code in expected_code:
                assert code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg
        else:
            assert expected_code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg

        if read_code < 400:
            pattern = ("Unexpected http success status code {0}, "
                       "The expected status code is {1}")
            if ((not isinstance(expected_code, list) and
                 (read_code != expected_code)) or
                    (isinstance(expected_code, list) and
                     (read_code not in expected_code))):
                details = pattern.format(read_code, expected_code)
                raise requests.exceptions.InvalidSchema(details)

    @classmethod
    def validate_response(cls, schema, body):
        """ 模式匹配校验

        :param schema:  schema模式
        :param body:    校验的内容
        :return:
        """
        if schema:
            if isinstance(schema, str):
                schema = json.loads(schema)
            try:
                # jsonschema.validate(body, schema,
                #                     cls=JSONSCHEMA_VALIDATOR,
                #                     format_checker=FORMAT_CHECKER)
                jsonschema.validate(body, schema)
            except jsonschema.ValidationError as ex:
                msg = ("返回模式匹配失败，错误原因 %s 返回的是 %s" % (ex.message, ex.instance))

                raise requests.exceptions.HTTPError(msg)
        else:
            if body:
                msg = ("HTTP response body should not exist (%s)" % body)
                raise requests.exceptions.HTTPError(msg)