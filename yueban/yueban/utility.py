# -*- coding:utf-8 -*-

"""
一些常用的封装好的功能、函数等
"""

import random
import uuid
import pickle


def simple_crypt(bs):
    """
    简单的字节加密方案
    :param bs:
    :return:
    """
    bs = bytearray(bs)
    for i in range(0, len(bs), 3):
        bs[i] ^= 0xab
    return bytes(bs)


def rc4(k, bs):
    """
    RC4流加密,加密解密同一个接口
    :param k: password
    :param bs: the bytes to be encrypted
    :return:
    """
    box = range(256)
    j = 0
    klen = len(k)
    for i in range(256):
        j = (j + box[i] + ord(k[i % klen])) % 256
        box[i], box[j] = box[j], box[i]
    out = bytearray(bs)
    i = j = 0
    for pos, ch in enumerate(out):
        i = (i + 1) % 256
        j = (j + box[i]) % 256
        box[i], box[j] = box[j], box[i]
        out[pos] = ch ^ box[(box[i] + box[j]) % 256]
    return bytes(out)


def weight_rand(weights):
    """
    :param weights:
    :return:
    """
    sum_weight = sum(weights)
    r = random.uniform(0, sum_weight)
    s = 0
    for i, w in enumerate(weights):
        s += w
        if r < s:
            return i
    return random.choice(range(len(weights)))


def weight_rand_dict(weight_dic):
    """
    根据字典中key值以及对应的随机权重随机选取一个key
    :param weight_dic:
    :return:
    """
    keys = weight_dic.keys()
    weights = [weight_dic[k] for k in keys]
    idx = weight_rand(weights)
    return keys[idx]


def cmp_version(v1, v2):
    """
    比较版本,版本格式为点分十进制,即xx.xx.xx
    :param v1:
    :param v2:
    :return: v1<v2, -1;    v2==v2, 0;  v1>v2, 1
    """
    if not v1:
        v1 = '0.0.0'
    if not v2:
        v2 = '0.0.0'
    v1_sp = [int(n) for n in v1.split('.')]
    v2_sp = [int(n) for n in v2.split('.')]
    if v1_sp < v2_sp:
        return -1
    elif v1_sp == v2_sp:
        return 0
    else:
        return 1


def format_time(sec, day_str='天', hour_str='小时', minute_str='分', second_str='秒'):
    """
    格式化（剩余）时间显示
    :param sec:
    :param day_str:
    :param hour_str:
    :param minute_str:
    :param second_str:
    :return:
    """
    s = ''
    sec = int(sec)
    day, left = divmod(sec, 86400)
    if day > 0:
        s += '{0:d}{1}'.format(day, day_str)
    hour, left = divmod(left, 3600)
    if hour > 0:
        s += '{0:d}{1}'.format(hour, hour_str)
    elif day > 0:
        s += '0{0}'.format(hour_str)
    minute, left = divmod(left, 60)
    if minute > 0:
        s += '{0}{1}'.format(minute, minute_str)
    elif day > 0 or hour > 0:
        s += '0{0}'.format(minute_str)
    s += '{0}{1}'.format(left, second_str)
    return s


def gen_uniq_id():
    """
    生成分布式-全局唯一ID
    :return:
    """
    return str(uuid.uuid1())


def dumps(obj):
    """
    通用的内部用的序列化函数
    :param obj:
    :return:
    """
    return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)


def loads(bs):
    """
    通用的内部用的反序列化函数
    :param bs:
    :return:
    """
    return pickle.loads(bs)
