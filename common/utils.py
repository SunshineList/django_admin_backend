# -*- coding: utf-8 -*-
"""
    @Time ： 2022/4/20 16:26
    @Auth ： wangzw
    @File ：utils.py
    @IDE ：PyCharm
    @Motto：ABC(Always Be Coding)
"""
import random
import re
import string


def random_valid_code(length=4):
    """
    随机验证码
    :param length:
    :return:
    """
    num_letter = string.ascii_letters + string.digits
    num_letter = re.sub('[BLOZSloz81025]', '', num_letter)
    return ''.join(random.sample(num_letter, length))