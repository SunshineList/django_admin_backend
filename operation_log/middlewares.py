import threading

from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from operation_log.models import OperationLog

_request = {}


def get_request_ip(request):
    """
    获取请求IP
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
        return ip
    ip = request.META.get('REMOTE_ADDR', '')
    return ip or 'unknown'


def get_verbose_name(queryset=None, view=None, model=None):
    """
    获取 操作对象的verbose_name
    :param queryset:
    :param view:
    :param model:
    :return:
    """
    try:
        if queryset and hasattr(queryset, 'model'):
            model = queryset.model
        elif view and hasattr(view.get_queryset(), 'model'):
            model = view.get_queryset().model
        elif view and hasattr(view.get_serializer(), 'Meta') and hasattr(
                view.get_serializer().Meta, 'model'):
            model = view.get_serializer().Meta.model
        if model:
            return getattr(model, '_meta').verbose_name
        else:
            model = queryset.model._meta.verbose_name
    except Exception as e:
        pass
    return model if model else ""


def current_user():
    tl = threading.current_thread()
    if tl not in _request:
        return None
    return _request[tl].user


class LoginUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _request[threading.current_thread()] = request


class OperationMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.op_id = None
        self._exclude_url = []  # 不记录的url
        self.is_open_record = getattr(settings, "IS_OPEN_RECORD", False)

    def __handle_password(self, params):
        """
        处理密码
        :param params:
        :return:
        """
        if params.get('password'):
            params['password'] = '*' * len(params['password'])
        return params

    def __handle_response(self, request):
        """
        处理参数保存日志
        """
        if self.op_id:
            params = request.method == 'GET' and request.GET or request.POST
            op_data = {
                "operation_ip": get_request_ip(request),
                "operation_user": not isinstance(current_user(), AnonymousUser) and current_user()
                or None,  # 操作用户
                "operation_type": {
                    'GET': '查询',
                    "POST": "新增",
                    "PUT": "修改",
                    "DELETE": "删除",
                }.get(request.method, None),  # 操作类型
                "operation_path": request.path,
                "operation_params": self.__handle_password(params),
            }
            OperationLog.objects.update_or_create(id=self.op_id, defaults=op_data)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        在视图函数调用前执行
        :param request:
        :param view_func:
        :param view_args:
        :param view_kwargs:
        :return:
        """

        for url in self._exclude_url:  # 判断是否在不记录的url列表中
            if url in request.path:
                return

        # 暂时只记录有queryset的api
        if hasattr(view_func, 'cls') and hasattr(view_func.cls, 'queryset'):
            vb_name = get_verbose_name(queryset=view_func.cls.queryset)
            if vb_name and self.is_open_record:
                instance = OperationLog.objects.create(operation_modular=vb_name)
                self.op_id = instance.id

    def process_response(self, request, response):
        """
        在请求处理后执行
        :param request:
        :param response:
        :return:
        """
        if self.is_open_record:
            self.__handle_response(request)
        return response
