from functools import wraps

from flask import jsonify, request
from marshmallow import ValidationError

def validate_schema(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            json_data = request.get_json()
            if not json_data:
                return jsonify({"message": "No input data provided"}), 400
            
            try:
                schema.load(json_data)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
