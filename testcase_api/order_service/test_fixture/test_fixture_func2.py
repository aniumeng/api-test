from common.db_handle import DbHandle
import pytest,requests


@pytest.fixture(scope='function')  # 或@pytest.fixture()
def resource_handle():
    db_ins=DbHandle()
    db_ins.connect()
    sql1 = "INSERT INTO test_data  SELECT * FROM test_data;"
    db_ins.query(sql1)
    sql2 = "SELECT COUNT(*) FROM test_data;"
    ret = db_ins.query(sql2)
    print(ret)
    print("配置测试资源完毕！！！")

    print("释放测试资源！！！")


def test_case1(setup):
    print("测试用例1")


def test_case2(teardown):
    print("测试用例子2")


if __name__ == '__main__':
    pytest.main()