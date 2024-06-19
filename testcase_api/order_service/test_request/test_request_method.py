import requests,pytest


def setup_module():
    print("准备测试数据")


def teardown_module():
    print("清理测试数据")


def setup_function():
    print("每条用例执行前的准备")


def teardown_function():
    print("每条用例执行后的收尾")


def test_login():
    url="http://127.0.0.1:9091/api/v1/user/login"
    json_data = {
        "authRequest": {
            "userName": "user01",
            "password": "pwd"
        }
    }
    response = requests.post(url=url,json=json_data)
    assert response.status_code == 200
    assert response.json()['message']=="login success"


def test_see_menu_list():
    """查看菜单 /api/v1/menu/list"""
    url="http://127.0.0.1:9091/api/v1/menu/list"
    headers = {
        "access_token": "3b6754f00bb0063071c5b71ce2b56b4ed0ce56a63493e785bea85b74c41ce200",
        "Content-Type": "application/json"
    }
    response = requests.get(url=url,headers=headers)
    assert response.json()['breakfast'][0].get('menu_name') == u'小笼包'


if __name__ == '__main__':
    pytest.main()