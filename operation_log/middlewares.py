from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from operation_log.models import OperationLog
from operation_log.utils import get_request_ip, get_verbose_name


class OperationMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.op_id = None
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
        if not self.op_id:
            params = request.method == 'GET' and request.GET or request.POST
            op_data = {
                "operation_ip": get_request_ip(request),
                "operation_user": getattr(request, 'user', None) or AnonymousUser(),  # 操作用户
                "operation_type": {
                    'GET': '查询',
                    "POST": "新增",
                    "PUT": "修改",
                    "DELETE": "删除",
                }.get(request.method, None),  # 操作类型
                "operation_path": request.path,
                "status": request.status_code == 200,
                "operation_params": self.__handle_password(params),
            }
            OperationLog.objects.create(**op_data)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        在视图函数调用前执行
        :param request:
        :param view_func:
        :param view_args:
        :param view_kwargs:
        :return:
        """
        if hasattr(view_func, 'queryset'):
            vb_name = get_verbose_name(queryset=view_func.queryset)
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
