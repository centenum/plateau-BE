from functools import wraps

from flask import jsonify, request
from marshmallow import ValidationError
from config import db

auth_collection = db.auth

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


def login_required(f):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'Authorization' not in request.headers:
                return jsonify({"message": "Unauthorized access"}), 401
            
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({"message": "Unauthorized access"}), 401
            
            authorized_user = auth_collection.find_one({"token": auth_header})
            if not authorized_user:
                return jsonify({"message": "Unauthorized access"}), 401
            # add the user to the request object
            request.user = authorized_user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
        