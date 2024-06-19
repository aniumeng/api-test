UI自动化测试说明

环境配置
1、安装有python3.6（包括pip）以上；chrome 65版本；pycharm或其它IDE工具；
2、安装requirements.txt中的第三方库；在cmd中使用 pip3 install -r requirement.txt

；如果慢，自行百度找解决方案

运行说明
1、查看conf中环境信息，确保配置是你需要的，里面有用户名等相关信息。
2、在cmd或pycharm的Terminal中运行pytest testcase\k8s\xxxx.py
      xxxx.py为你需要运行的测试用例文件
       默认为CI环境，如果需切换环境则在命令行中加上--env sit

场景接口自动化: 默认回收资源 如果不需要回收资源则在命令行中加上--rec False

附件说明
更深层使用说明，请联系Liu