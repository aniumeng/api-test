import requests,pytest


@pytest.fixture(scope='session')
def setup():
    print("配置测试资源")


@pytest.fixture(scope='session')
def teardown():
    print("释放测试资源")


def test_case1():
    print("测试用例1")


def test_case2(setup):
    print("测试用例2")


class TestCase(object):
    def test_case3(self):
        print("测试用例3")

    def test_case4(self):
        print("测试用例4")

    def test_case5(self):
        print("测试用例5")

    def test_case6(self):
        print("测试用例6")


if __name__ == '__main__':
    pytest.main()




