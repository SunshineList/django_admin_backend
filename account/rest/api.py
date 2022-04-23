import base64
import datetime
import uuid

from captcha.models import CaptchaStore
from captcha.views import captcha_image
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, exceptions, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from account.models import ImageCaptcha, UsersModel
from account.rest.serializers import LoginSerializer, UserInfoSerializer
from common.rest_utils import CustomCaptcha as imagescaptcha, ActiveMixin

from rest_framework.views import APIView
from rest_framework.response import Response

from common.auth import CsrfExemptSessionAuthentication
from common.utils import random_valid_code


# 这种验证码相当于是自己画出来的

class ImageCaptchaView(APIView):
    """获取登录管理后台的图片验证码"""
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):
        image_uuid = uuid.uuid4()
        random_captcha = random_valid_code(4)

        image_captcha = imagescaptcha()
        byte_image = image_captcha.generate(random_captcha, format='JPEG').getvalue()

        ImageCaptcha.objects.create(
            is_active=True,
            uuid=image_uuid,
            captcha=random_captcha,
            expire_time=datetime.datetime.now() +
                        datetime.timedelta(minutes=settings.STAFF_IMAGE_CAPTCHA_LIFETIME))

        return Response({
            'uuid': image_uuid,
            'image': 'data:image/jpeg;base64,%s' % base64.b64encode(byte_image).decode()
        })


# 这种获取验证码的方式是直接使用了 django-simple-captcha
class CaptchaView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        responses={
            '200': openapi.Response('获取成功')
        },
        security=[],
        operation_id='captcha-get',
        operation_description='验证码获取',
        tags=['验证码'],
    )
    def post(self, request):
        hashkey = CaptchaStore.generate_key()  # 生成验证码的答案
        captcha_id = CaptchaStore.objects.get(hashkey=hashkey)  # 把这个id返给前端
        image = captcha_image(request, hashkey)  # 生成验证码图片
        image_base = base64.b64encode(image.content)
        return Response(
            {"captcha_id": captcha_id.id, "image_base": "data:image/png;base64," + image_base.decode('utf-8')})


class LoginApiView(APIView):
    """ 登入 """

    permission_classes = (permissions.AllowAny,)
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = LoginSerializer

    schema = openapi.Schema(type=openapi.TYPE_OBJECT,
                            required=['username', 'password'],
                            tags=['登入'],
                            operation_description='登入',
                            properties={
                                'username':
                                    openapi.Schema('用户名', type=openapi.TYPE_STRING),
                                'password':
                                    openapi.Schema('密码', type=openapi.TYPE_STRING),
                                'captcha_id':
                                    openapi.Schema('captcha_id, 和图片验证码都传值时才会校验', type=openapi.TYPE_STRING),
                                'captcha':
                                    openapi.Schema('图片验证码，和captcha_id都传值时才会校验', type=openapi.TYPE_STRING),
                            })

    @swagger_auto_schema(request_body=schema, tags=['登入'], responses={'200': openapi.Response('token: xxxxx')})
    def post(self, request):
        """
        用户登录，获取 token
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({'token': token.key})

    @swagger_auto_schema(tags=['登出'], responses={204: openapi.Response('登出成功')})
    def delete(self, request, *args, **kwargs):
        """
        退出登录， 删除Token
        """
        if request.user.is_authenticated:
            Token.objects.filter(user=self.request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserInfoView(APIView):
    """
    获取用户信息
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserInfoSerializer

    @swagger_auto_schema(responses={'200': openapi.Response('用户信息')}, tags=['用户信息'])
    def get(self, request):
        """
        获取用户信息
        """
        user = request.user
        return Response(UserInfoSerializer(user, context={'request': request}).data)


class AccountViewSet(ActiveMixin, ModelViewSet):
    """
    用户列表
    """
    queryset = UsersModel.objects.all()
    serializer_class = UserInfoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    ordering = ('-date_joined',)
