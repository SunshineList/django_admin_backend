# -*- coding: utf-8 -*-
"""
这是django rest错误处理
"""

from django.db.models import ProtectedError
from django.http import Http404
from rest_framework.views import exception_handler, set_rollback
from rest_framework.response import Response

from rest_framework import exceptions

from django.conf import settings
from common.logger import LOG

def get_first_error_msg(error_messages, filed_name=None):
    if isinstance(error_messages, exceptions.ErrorDetail):
        return error_messages

    if isinstance(error_messages, dict):
        fields_name = list(error_messages.keys())[0]
        return get_first_error_msg(error_messages[fields_name], fields_name)

    if isinstance(error_messages, list):
        error_messages = [e for e in error_messages if e]
        return get_first_error_msg(error_messages[0], filed_name)

    LOG.info('errors msg:%s, error type:%s' % (error_messages, type(error_messages)))
    raise Exception(u'没有考虑到的数据格式')


def my_exception_handler(exc, context):  # 200 will never be here
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    if isinstance(exc, exceptions.APIException):
        set_rollback()
        errors_message = get_first_error_msg(exc.detail)
        error_data = {'error': errors_message}

        if settings.DEBUG or getattr(settings, 'TESTING'):
            error_data['dev'] = exc.detail  # 只有开发阶段才能看到所有的字段错误信息
        LOG.debug('bad request info data: %s' % error_data)
        return Response(error_data, status=exc.status_code)

    if isinstance(exc, ProtectedError):
        error_data = {'error': "该条记录存在保护外键，无法删除"}
        if settings.DEBUG or getattr(settings, 'TESTING'):
            error_data['dev'] = str(exc)
        return Response(error_data, status=400)

    if isinstance(exc, Http404):
        error_data = {'error': '未找到记录'}
        if settings.DEBUG or getattr(settings, 'TESTING'):
            error_data['dev'] = '未找到记录'
        return Response(error_data, status=404)
    return exception_handler(exc, context)
