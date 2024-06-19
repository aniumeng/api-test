#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pymysql
import time

log = logging.getLogger(__name__)


class DbHandle(object):
    """mysql数据库操作"""

    def __init__(self, host=None, port=None, user=None, password=None, db=None):
        self.host = host or '127.0.0.1'
        self.port = port or 3306
        self.user = user or 'root'
        self.password = password or '123456'
        self.db = db or 'testdb'
        self._con = None

    @property
    def connect(self):
        if self._con is None:
            self._con = pymysql.Connect(
                host=self.host, port=self.port,
                user=self.user, passwd=self.password,
                db=self.db, charset='utf8'
            )
        return self._con

    def query(self, sql):
        try:
            with self.connect.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        except Exception as e:
            log.info(e)
            self.connect.close()
            self._con = None

    def query2dict(self, sql):
        cursor = self.connect.cursor()
        log.info(sql)
        cursor.execute(sql)
        result = []
        description = [x[0] for x in cursor.description]
        for x in cursor.fetchall():
            result.append(dict(zip(description, x)))
        return result


def main():
    db_ins = DbHandle(host='127.0.0.1', user='root', password='123456', db='testdb')
    sql1 = "INSERT INTO test_data  SELECT * FROM test_data;"
    db_ins.query(sql1)
    time.sleep(2)
    sql2 = "SELECT COUNT(*) FROM test_data;"
    ret = db_ins.query(sql2)
    print(ret)
    db_ins.connect.close()


if __name__ == '__main__':
    main()