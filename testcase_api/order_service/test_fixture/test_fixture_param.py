import pytest,allure,requests,yaml
from common.db_handle import DbHandle
import time


f = open("/conf/test_data.yaml", encoding="utf-8")
json_data = yaml.safe_load(f)['authRequest']


@allure.feature("菜单管理模块")
class TestMenuApi(object):
    @pytest.fixture(scope="function")
    def get_db_data(self):
        try:
            db_ins = DbHandle(host='127.0.0.1', user='root', password='123456', db='testdb')
            sql1 = "INSERT INTO test_data  SELECT * FROM test_data;"
            db_ins.query(sql1)
            time.sleep(2)
            sql2 = "SELECT COUNT(*) FROM test_data;"
            ret = db_ins.query(sql2)
            print(ret)
            print("测试数据准备")
            db_ins.connect.close()
        except Exception as e:
            print(e)


    @pytest.mark.parametrize("userName,password", [(json_data.get('userName'), json_data.get('password'))])
    @allure.story("用户登录接口")
    def test_login(self,userName,password):
        """用户登录"""
        url = "http://127.0.0.1:9091/api/v1/user/login"
        #print("获取接口参数 userName:{}-password:{}".format(userName, password))
        json_data = {
            "authRequest": {
                "userName": userName,
                "password": password
            }
        }
        response = requests.post(url=url, json=json_data)
        access_token = response.json()['access_token']
        assert response.status_code == 200
        assert response.json()['message'] == "login success"
        return access_token


    @allure.story("查看菜单接口")
    def test_see_menu_list(self,get_db_data):
        """查看菜单"""
        url="http://127.0.0.1:9091/api/v1/menu/list"
        access_token = self.test_login(json_data.get('userName'),json_data.get('password'))
        headers = {
            "access_token": access_token,
            "Content-Type": "application/json"
        }
        response = requests.get(url=url,headers=headers)
        assert response.json()['breakfast'][0].get('menu_name') == u'小笼包'


if __name__ == '__main__':
    #pytest.main(['-s', '-q', '--alluredir', './report/xml'])
    pytest.main()