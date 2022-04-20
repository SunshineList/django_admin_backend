from datetime import datetime, timedelta

from captcha.models import CaptchaStore
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.models import ImageCaptcha, UsersModel


# 自己画的验证码的序列化器实现方式
class LoginOneSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, error_messages={'blank': u'用户名不能为空'})
    password = serializers.CharField(style={'input_type': 'password'},
                                     required=True,
                                     error_messages={'blank': u'密码不能为空'})
    uuid = serializers.UUIDField(required=False)
    captcha = serializers.CharField(required=False, max_length=10)

    def validate(self, attrs):
        username, password, received_captcha, image_uuid = attrs['username'], attrs[
            'password'], attrs.get('captcha'), attrs.get('uuid')

        if received_captcha and image_uuid:
            img_captcha = ImageCaptcha.objects.filter(uuid=image_uuid,
                                                      expire_time__gt=datetime.now()).first()

            if not img_captcha:
                raise ValidationError(u'图片验证码已失效')

            ImageCaptcha.objects.filter(pk=img_captcha.pk).update(is_active=False)
            if not img_captcha.is_active:
                raise ValidationError(u'图片验证码已失效')
            if img_captcha.captcha.lower() != received_captcha.lower():
                raise ValidationError(u'图片验证码输入错误')

        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError(u'用户名或者密码错误')

        attrs['user'] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, error_messages={'blank': u'用户名不能为空'})
    password = serializers.CharField(style={'input_type': 'password'},
                                     required=True,
                                     error_messages={'blank': u'密码不能为空'})
    captcha_id = serializers.IntegerField(required=False)
    captcha = serializers.CharField(required=False, max_length=10)

    def validate(self, attrs):
        username, password, received_captcha, captcha_id = attrs['username'], attrs[
            'password'], attrs.get('captcha'), attrs.get('captcha_id')

        cs_instance = CaptchaStore.objects.filter(id=captcha_id).first()

        if not cs_instance:
            raise ValidationError(u'验证码错误')

        # 默认5分钟过期
        five_minute_ago = datetime.now() - timedelta(hours=0, minutes=settings.STAFF_IMAGE_CAPTCHA_LIFETIME, seconds=0)

        if five_minute_ago > cs_instance.expiration:
            cs_instance.delete()  # 删除过期的验证码
            raise ValidationError(u'验证码已过期')

        # 判断验证码是否正确
        received_captcha = received_captcha.lower()

        if cs_instance.response.lower() == received_captcha:
            cs_instance.delete()
        else:
            raise ValidationError(u'验证码错误')

        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError(u'用户名或者密码错误')

        attrs['user'] = user

        return attrs


# 用户个人信息的序列化器
class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser',
                  'date_joined', 'mobile', 'avatar', 'user_type', 'get_user_type_display', 'name')
