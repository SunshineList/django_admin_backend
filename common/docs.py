# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from drf_yasg import openapi
from drf_yasg.inspectors import ChoiceFieldInspector, NotHandled
from drf_yasg.inspectors.field import get_parent_serializer, get_model_field, get_basic_type_info, \
    get_basic_type_info_from_hint
from drf_yasg.utils import field_value_to_representation

import json
"""
drf-yasg 文档自定义
"""


class CustomChoiceFieldInspector(ChoiceFieldInspector):
    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type,
                                                                use_references, **kwargs)
        if isinstance(field, serializers.ChoiceField):
            enum_type = openapi.TYPE_STRING
            enum_values = []

            if isinstance(field, serializers.MultipleChoiceField):
                for choice in field.choices.keys():
                    enum_values.append(field_value_to_representation(field, [choice])[0])
            else:
                for value, name in field.choices.items():
                    choice = json.dumps({
                        'name': name,
                        'value': value
                    },
                                        ensure_ascii=False,
                                        sort_keys=True)
                    enum_values.append(choice)

            # for ModelSerializer, try to infer the type from the associated model field
            serializer = get_parent_serializer(field)
            if isinstance(serializer, serializers.ModelSerializer):
                model = getattr(getattr(serializer, 'Meta'), 'model')
                # Use the parent source for nested fields
                model_field = get_model_field(model, field.source or field.parent.source)
                # If the field has a base_field its type must be used
                if getattr(model_field, "base_field", None):
                    model_field = model_field.base_field
                if model_field:
                    model_type = get_basic_type_info(model_field)
                    if model_type:
                        enum_type = model_type.get('type', enum_type)
            else:
                # Try to infer field type based on enum values
                enum_value_types = {type(v) for v in enum_values}
                if len(enum_value_types) == 1:
                    values_type = get_basic_type_info_from_hint(next(iter(enum_value_types)))
                    if values_type:
                        enum_type = values_type.get('type', enum_type)

            if isinstance(field, serializers.MultipleChoiceField):
                result = SwaggerType(
                    type=openapi.TYPE_ARRAY,
                    items=ChildSwaggerType(type=enum_type, enum=enum_values))
                if swagger_object_type == openapi.Parameter:
                    if result['in'] in (openapi.IN_FORM, openapi.IN_QUERY):
                        result.collection_format = 'multi'
            else:
                result = SwaggerType(type=enum_type, enum=enum_values)

            return result

        return NotHandled
