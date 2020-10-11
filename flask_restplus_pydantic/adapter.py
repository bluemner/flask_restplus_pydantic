""" Flask Adapter
"""
import datetime
import decimal
import re
from typing import List, Union

from flask_restplus import Api, Model, fields
from pydantic import BaseModel


class FlaskRestPlusPydanticAdapter:
    """
        Adapter for flask rest plus pydantic

        :param api flask_restplus.Api: flask_restplus Api instance to which is needed for \
                    api.model function call
    """

    api: Api

    def __init__(self, api: Api):
        self.api = api

    @staticmethod
    def python_to_flask(python_type: type) -> str:
        """ Converts python types to flask types
            :param type python_type: type that is to be converted into flask type
            :return: flask type represented as a string
            :rtype: str
        """
        if python_type is int:
            return 'Integer'
        if python_type in [float, decimal.Decimal]:
            return 'Float'
        if python_type is bool:
            return 'Boolean'
        if python_type is datetime.datetime:
            return 'DateTime'
        if python_type is datetime.date:
            return 'Date'
        return 'String'

    def pydantic_model(self, base_model: BaseModel) -> Model:
        """
            Pydantic model 

            :param base_model pydantic.BaseModel: Pydantic base model the will be
                converted to use flask restplus Model
            :return: Model instance
            :rtype: flask_restplus.Model
        """
        result = {}
        entity_name = base_model.__model__ if hasattr(base_model, '__model__') else \
            re.sub(r'(?<!^)(?=[A-Z])', '_', base_model.__name__).lower()

        for name, python_type in base_model.__annotations__.items():
            if '__' in name:
                continue
            regex = None
            description = ""
            required = True
            field_data = dict(base_model.__fields__.items())[name]

            if field_data is not None and hasattr(field_data, 'field_info'):
                regex = field_data.field_info.regex
                description = field_data.field_info.description
                required = field_data.required
                # TODO implement all field attributes

            if hasattr(python_type, '__origin__') and python_type.__origin__ == Union:
                args = list(python_type.__args__)
                if type(None) in args:
                    required = False
                    args.remove(type(None))
                python_type = args[0]

            if hasattr(python_type, '__origin__') and python_type.__origin__ in [List, list]:
                args = list(python_type.__args__)
                current_type = self.python_to_flask(args[0])
                result[name] = fields.List(getattr(fields, current_type)(
                    readOnly=False, description=description, required=required, pattern=regex))
                continue
            if hasattr(python_type, '__bases__') and BaseModel in python_type.__bases__:
                result[name] = fields.Nested(self.pydantic_model(python_type))
                continue
            current_type = self.python_to_flask(self.python_to_flask)
            result[name] = getattr(fields, current_type)(
                readOnly=False, description=description, required=required, pattern=regex)

        return self.api.model(entity_name, result)
