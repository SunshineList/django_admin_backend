import base64
import datetime
import random
import re
import string
import uuid

from captcha.models import CaptchaStore
from captcha.views import captcha_image
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, exceptions
from rest_framework.authentication import BasicAuthentication
from rest_framework.viewsets import ModelViewSet

from account.models import ImageCaptcha
from common.utils import CustomCaptcha as imagescaptcha

from rest_framework.views import APIView
from rest_framework.response import Response

from common.auth import CsrfExemptSessionAuthentication


# 这种验证码相当于是自己画出来的
class ImageCaptchaView(APIView):
    """获取登录管理后台的图片验证码"""
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def random_valid_code(self, length=4):
        """
        随机验证码
        :param length:
        :return:
        """
        num_letter = string.ascii_letters + string.digits
        num_letter = re.sub('[BLOZSloz81025]', '', num_letter)
        return ''.join(random.sample(num_letter, length))

    def post(self, request):
        image_uuid = uuid.uuid4()
        random_captcha = self.random_valid_code(4)

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
    )
    def get(self, request):
        hashkey = CaptchaStore.generate_key()
        id = CaptchaStore.objects.filter(hashkey=hashkey).first().id
        image = captcha_image(request, hashkey)
        # 将图片转换为base64
        image_base = base64.b64encode(image.content)
        json_data = {"key": id, "image_base": "data:image/png;base64," + image_base.decode('utf-8')}
        return Response(data=json_data)
