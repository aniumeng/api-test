#!usr/bin/env python
# -*- coding:utf-8 -*-


def is_exist_get_values(l, expect, exist_field, query_field_list=None):
    """
       :param l:
       :param expect: 预期值
       :param exist_field: 预期字段
       :param query_field_list: 预期行中需查询的参数列表
       :return:
    """
    query_set = []
    for i in l:
        if i.get(exist_field) == expect:
            if query_field_list:

                for q in query_field_list:
                    query_set.append(i.get(q))

                return True, query_set
            else:
                return True

    return False, query_set if query_field_list else False


def is_exist_get_value(l, expect, exist_field, query_field=None):
    """

    :param l:
    :param expect: 预期值
    :param exist_field: 预期字段
    :param query_field: 预期行中需查询的参数
    :return:
    """

    for i in l:
        if i.get(exist_field) == expect:
            if query_field:
                return True, i.get(query_field)
            else:
                return True
    return False, None
