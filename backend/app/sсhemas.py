from app.extension import ma
from marshmallow import validate, ValidationError, fields, validates
from datetime import datetime

class UserSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, error='имя не может быть пустым'))
    email = fields.Email(required=True, validate=validate.Length(min=3, error='имэил не может быть таким коротким'))
    password = fields.Str(required=True, load_only=True, validate=[
        validate.Length(min=8, error='пароль не может быть короче 8 символов')
    ])
    create_date = fields.DateTime(dump_only=True)

    @validates('password')
    def validate_password(self, value, **kwargs):
        flag_alpha = any(c.isalpha() for c in value)
        flag_digit = any(c.isdigit() for c in value)
        if not (flag_alpha and flag_digit):
            raise ValidationError('пароль должен содержать хотя бы одну букву и одну цифру')

user_schema = UserSchema()
users_schema = UserSchema(many=True)