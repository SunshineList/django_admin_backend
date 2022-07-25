# -*- coding: utf-8 -*-
"""
    @Time ： 2022/4/19 18:25
    @Auth ： wangzw
    @File ：custom_utils.py
    @IDE ：PyCharm
    @Motto：ABC(Always Be Coding)
"""

# 自定义验证码样式
import random
import re
import uuid
import copy

import django_filters
import requests
import six
from PIL import ImageFilter, Image
from PIL.ImageDraw import Draw
from captcha.image import ImageCaptcha
from dateutil.relativedelta import relativedelta
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.core.validators import URLValidator, MaxValueValidator, MinValueValidator, EMPTY_VALUES
from django.utils.timezone import now as django_now
from django.db import models
from django.db.models import JSONField

from django.utils.functional import lazy
from django_filters.fields import Lookup
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from django_filters.widgets import QueryArrayWidget
from drf_extra_fields.fields import Base64ImageField, Base64FileField
from imagekit.models import ProcessedImageField
from rest_framework import exceptions, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import DestroyModelMixin
from rest_framework.response import Response
from rest_framework.serializers import SerializerMetaclass
from rest_framework import fields
from django.utils.translation import ugettext_lazy as _


class CustomCaptcha(ImageCaptcha):
    def create_captcha_image(self, chars, color, background):
        """Create the CAPTCHA image itself.

        :param chars: text to be generated.
        :param color: color of the text.
        :param background: color of the background.

        The color should be a tuple of 3 numbers, such as (0, 255, 255).
        """

        table = []
        for i in range(256):
            table.append(i * 1.97)

        image = Image.new('RGB', (self._width, self._height), background)
        draw = Draw(image)

        def _draw_character(c):
            font = random.choice(self.truefonts)
            w, h = draw.textsize(c, font=font)

            dx = random.randint(0, 4)
            dy = random.randint(0, 6)
            im = Image.new('RGBA', (w + dx, h + dy))
            Draw(im).text((dx, dy), c, font=font, fill=color)
            return im

        images = []
        for c in chars:
            images.append(_draw_character(c))

        text_width = sum([im.size[0] for im in images])

        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars))
        rand = int(0.25 * average)
        offset = int(average * 0.1)

        for im in images:
            w, h = im.size
            mask = im.convert('L').point(table)
            image.paste(im, (offset, int((self._height - h) / 2)), mask)
            offset = offset + w + random.randint(-rand, 0)

        if width > self._width:
            image = image.resize((self._width, self._height))

        return image

    def generate_image(self, chars):
        """Generate the image of the given characters.

        :param chars: text to be generated.
        """
        background = self.random_color(238, 255)
        color = self.random_color(0, 200, random.randint(220, 255))
        im = self.create_captcha_image(chars, color, background)
        # self.create_noise_dots(im, color)
        self.create_noise_curve(im, color)
        im = im.filter(ImageFilter.SMOOTH)
        return im

    def random_color(self, start, end, opacity=None):
        """
        生成随机颜色
        """
        red = random.randint(start, end)
        green = random.randint(start, end)
        blue = random.randint(start, end)
        if opacity is None:
            return (red, green, blue)
        return (red, green, blue, opacity)


class DateTimeField(fields.DateTimeField):
    def to_internal_value(self, value):
        if self.allow_null and not value:
            return None

        return super(DateTimeField, self).to_internal_value(value)


class FloatField(fields.FloatField):
    def to_internal_value(self, value):
        if value in ['', None, 'null']:
            return None

        return super(FloatField, self).to_internal_value(value)


class CharField(fields.CharField):
    def to_internal_value(self, data):
        if data in ['', None, 'null']:
            return None
        return super(CharField, self).to_internal_value(data)


class IntegerField(fields.Field):
    default_error_messages = {
        'invalid': _('A valid integer is required.'),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
        'max_string_length': _('String value too large.')
    }
    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.
    re_decimal = re.compile(r'\.0*\s*$')  # allow e.g. '1.0' as an int, but not '1.2'

    def __init__(self, **kwargs):
        self.max_value = kwargs.pop('max_value', None)
        self.min_value = kwargs.pop('min_value', None)
        super(IntegerField, self).__init__(**kwargs)

        if not self.allow_null:
            self.validator()

    def to_internal_value(self, data):

        if data in ['', None, 'null']:
            return None

        self.validator()

        if isinstance(data, six.text_type) and len(data) > self.MAX_STRING_LENGTH:
            self.fail('max_string_length')

        try:
            data = int(self.re_decimal.sub('', str(data)))
        except (ValueError, TypeError):
            self.fail('invalid')
        return data

    def to_representation(self, value):
        return int(value)

    def validator(self):

        if self.max_value is not None:
            message = lazy(self.error_messages['max_value'].format,
                           six.text_type)(max_value=self.max_value)
            self.validators.append(MaxValueValidator(self.max_value, message=message))
        if self.min_value is not None:
            message = lazy(self.error_messages['min_value'].format,
                           six.text_type)(min_value=self.min_value)
            self.validators.append(MinValueValidator(self.min_value, message=message))


class CustomBase64FileField(Base64FileField):
    @property
    def ALLOWED_TYPES(self):
        audio = [
            'MP3', 'AAC', 'WAV', 'WMA', 'CDA', 'FLAC', 'M4A', 'MID', 'MKA', 'MP2', 'MPA', 'MPC',
            'APE', 'OFR', 'OGG', 'RA', 'WV', 'TTA', 'AC3', 'DTS'
        ]
        video = [
            'AVI', 'RMVB', 'RM', 'ASF', 'DIVX', 'MPG', 'MPEG', 'MPE', 'WMV', 'MP4', 'MKV', 'VOB'
        ]
        package = ['APK']
        return audio + video + package

    def get_file_extension(self, filename, decoded_file):
        return filename.rsplit('.', 1)[-1].upper()

    def to_internal_value(self, base64_or_url):
        if isinstance(base64_or_url, six.string_types) and base64_or_url.rsplit(
                '.', 1)[-1].upper() in self.ALLOWED_TYPES:
            return base64_or_url.split(settings.MEDIA_URL)[-1]
        return super(CustomBase64FileField, self).to_internal_value(base64_or_url)


class CustomBase64ImageField(Base64ImageField):
    def __init__(self, *args, **kwargs):
        self.url_validator = URLValidator()
        super(CustomBase64ImageField, self).__init__(*args, **kwargs)

    @property
    def ALLOWED_TYPES(self):
        img_types = ('jpeg', 'jpg', 'png', 'gif', 'JPEG', 'JPG', 'PNG', 'GIF')
        return img_types

    def to_internal_value(self, base64_data):
        if isinstance(
                base64_data,
                InMemoryUploadedFile) and base64_data.name.split('.')[-1] in self.ALLOWED_TYPES:
            return super(fields.ImageField, self).to_internal_value(base64_data)

        if isinstance(base64_data, six.string_types) and base64_data.rsplit(
                '.', 1)[-1] in self.ALLOWED_TYPES:

            request = self.context.get('request')
            media_url = settings.MEDIA_URL
            if request is not None:
                host = '{scheme}://{host}'.format(scheme=request.scheme, host=request.get_host())
                if not media_url.startswith(host):
                    media_url = host + media_url

            if (self._verify_local_url(base64_data) and base64_data.startswith(media_url)):
                return base64_data.split(settings.MEDIA_URL)[-1]

            return self.to_local_img_path(base64_data).split(settings.MEDIA_URL)[-1]

        return super(CustomBase64ImageField, self).to_internal_value(base64_data)

    def to_local_img_path(self, url):
        """第三方图片路径转为本地图片路径"""

        url = self._valid_url(url)
        if not url:
            raise exceptions.ValidationError('图片路径不正确，请检查上传的图片路径是否正确')

        try:
            data = requests.get(url, timeout=3)
        except (requests.ConnectionError, requests.Timeout):
            raise exceptions.ValidationError('连接超时，无法获取第三方的图片数据，请检查上传的图片路径是否正确')
        except Exception as e:
            raise exceptions.ValidationError('未知错误，无法获取第三方的图片数据，请检查上传的图片路径是否正确')

        img = SimpleUploadedFile(
            '%s.%s' % (''.join(str(uuid.uuid1()).split('-')), url.rsplit('.')[-1]), data.content)

        return default_storage.url(default_storage.save(img.name, img))

    def _valid_url(self, url):
        try:
            self.url_validator(url)
        except ValidationError as e:
            return
        return url

    def _verify_local_url(self, url):
        """验证图片路径是否为本地路径"""

        if '*' in settings.ALLOWED_HOSTS:
            return True

        request = self.context.get('request')
        if request is None:
            return False

        scheme = '{scheme}://'.format(scheme=request.scheme)

        is_local_url = False

        for host in settings.ALLOWED_HOSTS:
            if url.startswith('%s%s' % (scheme, host)):
                is_local_url = True
        return is_local_url


class CustomSerializerMetaclass(SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        created_cls = super(CustomSerializerMetaclass, cls).__new__(cls, name, bases, attrs)
        return created_cls


class RecursiveField(serializers.Serializer):
    """
    自定义model递归的 serializer ，如model设计中，存在 ForeignKey 是 self 的情况，需要分级显示时
    """
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CustomJsonField(serializers.JSONField):
    """
    自定义JSONField返回值
    """
    def to_representation(self, value):
        return value


# @six.add_metaclass(CustomSerializerMetaclass)
class CustomModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        include_fields = kwargs.pop('fields', None)

        super(CustomModelSerializer, self).__init__(*args, **kwargs)
        self.serializer_field_mapping[models.ImageField] = CustomBase64ImageField
        self.serializer_field_mapping[models.DateTimeField] = DateTimeField
        self.serializer_field_mapping[models.FloatField] = FloatField
        self.serializer_field_mapping[models.IntegerField] = IntegerField
        self.serializer_field_mapping[ProcessedImageField] = CustomBase64ImageField
        self.serializer_field_mapping[models.FileField] = CustomBase64FileField
        self.serializer_field_mapping[JSONField] = CustomJsonField
        # 为了本地开发方便，image字段不用base64
        # if getattr(settings, 'ENV', None) == 'DEVELOP':
        #     self.serializer_field_mapping[models.ImageField] = fields.ImageField

        if include_fields is not None:
            allowed = set(include_fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class CustomModelPrimaryKeySerializer(serializers.ModelSerializer,
                                      serializers.PrimaryKeyRelatedField):
    def __init__(self, queryset, *args, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        self.queryset = queryset
        super(CustomModelPrimaryKeySerializer, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class CustomFileField(serializers.FileField):
    def to_internal_value(self, data):
        if isinstance(data, six.string_types):
            return data.split(settings.MEDIA_URL)[-1]
        return super(CustomFileField, self).to_internal_value(data)


class CustomListFilesField(serializers.ListField):
    def __init__(self, img_field_name='img', *args, **kwargs):
        self.img_field_name = img_field_name
        super(CustomListFilesField, self).__init__(*args, **kwargs)

    def to_representation(self, relate_field):
        if hasattr(relate_field, 'all'):
            return super(CustomListFilesField, self).to_representation(
                [getattr(i, self.img_field_name) for i in relate_field.all()])

        return super(CustomListFilesField, self).to_representation(relate_field)


class StringListField(serializers.ListField):
    def to_representation(self, data):
        try:
            data = eval(data)
        except Exception as e:
            return None
        return data

    def to_internal_value(self, data):
        return str(super(StringListField, self).to_internal_value(data))


# django filter 的bug，前端传boolean类型错误
class NullBooleanSelect(forms.NullBooleanSelect):
    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return {
            '2': True,
            True: True,
            'True': True,
            'true': True,
            '3': False,
            'False': False,
            False: False,
            'false': False,
            '0': False,
            '1': True,
        }.get(value)


class NullBooleanField(forms.NullBooleanField):
    widget = NullBooleanSelect


class BooleanFilter(django_filters.BooleanFilter):
    field_class = NullBooleanField


FILTER_FOR_DBFIELD_DEFAULTS[models.BooleanField] = {'filter_class': BooleanFilter}


# drf 的action扩展
class ActiveMixin(object):
    """
    设置状态
    """
    ACTIVE_FIELD_NAME = 'is_active'

    @action(methods=['post'], detail=True)
    def active(self, request, *args, **kwargs):
        is_active = request.data.get('is_active')
        instance = self.get_object()
        # instance.is_active = bool(is_active)
        setattr(instance, self.ACTIVE_FIELD_NAME, bool(is_active))
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DataForHospitalMixin(object):
    data_for_hospital_filter_param = 'hospital'

    def filter_queryset(self, queryset):
        user = self.request.user

        if not user.is_authenticated() or not self.request.user.hospital:
            return super(DataForHospitalMixin, self).filter_queryset(queryset)

        hospital = self.request.user.hospital

        if self.data_for_hospital_filter_param == 'id' and hospital:
            queryset = queryset.filter(**({self.data_for_hospital_filter_param: hospital.id}))
        elif hospital:
            queryset = queryset.filter(**({self.data_for_hospital_filter_param: hospital}))
        return super(DataForHospitalMixin, self).filter_queryset(queryset.distinct())


class DataForOwnerMinxin(object):
    owner_field_name = 'owner'

    def get_queryset(self):
        queryset = super(DataForOwnerMinxin, self).get_queryset()

        if not self.request.user.is_authenticated():
            return queryset

        if hasattr(queryset.model, self.owner_field_name):
            return queryset.filter(**{self.owner_field_name: self.request.user})
        return queryset.filter(user=self.request.user)


class CustomDestroyModelMixin(DestroyModelMixin):
    """
    覆盖原有删除，做标记删除
    """
    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()


# django_filter 的扩展


class FormRangeMixin(object):
    def to_python(self, value):
        """
        datalist 的验证
        """

        if value in self.empty_values:
            return None

        # 前端传入的无序时间，需要重新排序
        value.sort()

        date_list = []
        for d in value:
            df = super(FormRangeMixin, self).to_python(d)
            if not df:
                return None
            date_list.append(df)

        # 如果等于1. 说明值重复了
        if len(date_list) == 1:
            date_list.append(date_list[0])

        return sorted(date_list)


class FormsDateField(FormRangeMixin, forms.DateField):
    pass


class FormsDatetimeField(FormRangeMixin, forms.DateTimeField):
    pass


class DateListFilter(django_filters.DateFilter):
    field_class = FormsDateField

    def __init__(self, widget=QueryArrayWidget, **kwargs):
        super(DateListFilter, self).__init__(widget=widget, **kwargs)


class DateTimeListFilter(django_filters.DateFilter):
    field_class = FormsDatetimeField

    def __init__(self, widget=QueryArrayWidget, **kwargs):
        super(DateTimeListFilter, self).__init__(widget=widget, **kwargs)


class IntegerFilter(django_filters.CharFilter):
    field_class = forms.IntegerField


class MonthFilter(IntegerFilter):
    """
    根据月份查询。
    C端非常多这种一个月内、三个月内、六个月内的数据查询
    """
    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()

        month = abs(value)
        value = django_now() - relativedelta(months=month)

        qs = self.get_method(qs)(**{'%s__%s' % (self.field_name, lookup): value})
        return qs


class AllMixin(object):
    LIMIT = 2000

    # @swagger_auto_schema(responses={status.HTTP_200_OK: openapi.Response('返回数据', AllMixin.serializer_class)})
    @action(methods=['get'], detail=False)
    def all(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.count() > self.LIMIT:
            raise exceptions.ValidationError('数据太多，不能一次性获取%s条数据，该情况请做分页处理' % self.LIMIT)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'detail': serializer.data})


class ExportMixin(object):
    LIMIT = 20000

    @action(methods=['get'], detail=False)
    def export(self, request, *args, **kwargs):
        """
        导出，只给data数据，前端自己根据data生成文件，不带分页
        """

        queryset = self.filter_queryset(self.get_queryset())
        if queryset.count() > self.LIMIT:
            raise exceptions.ValidationError('数据太多，不能一次性导入%s条数据！' % self.LIMIT)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'detail': serializer.data})
