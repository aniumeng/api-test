import requests
import os


# json_data = {
# 	"authRequest": {
# 		"userName": "user01",
# 		"password": "pwd"
# 	}
# }
#
# ret = requests.post(url='http://127.0.0.1:9091/api/v1/user/login',json=json_data)
#
#
# print(type(ret.json().get('access_token')))
# headers = {
#   'access_token': ret.json().get('access_token'),
#   'Content-Type': 'application/json'
# }
#
# ret2 = requests.get(url='http://127.0.0.1:9091/api/v1/menu/list',headers=headers)
# print(ret2.json())

env = os.getenv('env').lower()
print(env)