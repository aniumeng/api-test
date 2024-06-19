import requests,pytest


class TestSetup2TeardownCase1(object):

    def setup_class(self):
        print("测试类执行前的准备")

    def teardown_class(self):
        print("测试类执行后的收尾")

    def setup_method(self):
        print("测试方法执行前的准备")

    def teardown_method(self):
        print("测试方法执行后的收尾")

    def test_login(self):
        url = "http://127.0.0.1:9091/api/v1/user/login"
        json_data = {
            "authRequest": {
                "userName": "user01",
                "password": "pwd"
            }
        }
        response = requests.post(url=url, json=json_data)
        assert response.status_code == 200
        assert response.json()['message'] == "login success"

    def test_see_menu_list(self):
        """查看菜单 /api/v1/menu/list"""
        url = "http://127.0.0.1:9091/api/v1/menu/list"
        headers = {
            "access_token": "3b6754f00bb0063071c5b71ce2b56b4ed0ce56a63493e785bea85b74c41ce200",
            "Content-Type": "application/json"
        }
        response = requests.get(url=url, headers=headers)
        assert response.json()['breakfast'][0].get('menu_name') == u'小笼包'


class TestSetup2TeardownCase2(object):
    def test_one(self):
        assert 1==1

    def test_two(self):
        assert 1==2


if __name__ == '__main__':
    pytest.main()