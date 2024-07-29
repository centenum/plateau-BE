from flask import Blueprint, request, jsonify
from config import db, SENDCHAMP_PUBLIC_KEY

import string, random, uuid
from datetime import datetime, timedelta, timezone
import bcrypt, requests
from flasgger import swag_from

routes_authentication = Blueprint('authentication_routes', __name__)

users_collection = db.users
auth_collection = db.auth

# Helper function to generate a random password
def generate_password(length=8):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

# Helper function to generate a unique token
def generate_token():
    return str(uuid.uuid4())

# Helper function to send OTP via sendChamp
def send_champ_otp(phone_number, first_name):
    url = 'https://api.sendchamp.com/api/v1/verification/create'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SENDCHAMP_PUBLIC_KEY}'
    }
    data = {
        'channel': 'sms',
        'sender': 'Sendchamp',
        'token_type': 'numeric',
        'token_length': '4',
        'expiration_time': 10,
        'customer_mobile_number': phone_number,
        'meta_data': {'first_name': first_name}
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()['data']
        return result['reference'], result['token']
    else:
        raise Exception('Failed to send OTP')
    




# Endpoint to register users (APO or PO)
@routes_authentication.route('/register', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'firstName': {'type': 'string'},
                    'lastName': {'type': 'string'},
                    'email': {'type': 'string'},
                    'phoneNumber': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['APO', 'PO']}
                },
                'required': ['firstName', 'lastName', 'email', 'phoneNumber']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'User registered successfully',
            'examples': {
                'application/json': {
                    'message': 'User registered successfully',
                    'password': 'generated-password'
                }
            }
        }
    }
})
def register_user():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    role = data.get('role', 'APO')  # Default role is APO if not specified
    password = generate_password()
    created_at = datetime.now(timezone.utc)

    # Hash the password with bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': hashed_password,
        'createdAt': created_at,
        'role': role
    }

    users_collection.insert_one(user)
    return jsonify({'message': 'User registered successfully', 'password': password}), 201

# Endpoint for user login
@routes_authentication.route('/login', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['email', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'OTP sent successfully',
            'examples': {
                'application/json': {
                    'message': 'OTP sent successfully'
                }
            }
        },
        401: {
            'description': 'Invalid email or password',
            'examples': {
                'application/json': {
                    'message': 'Invalid email or password'
                }
            }
        }
    }
})
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email})
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        # Generate token and store in auth collection
        token = generate_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
        auth_record = {
            'user_id': user['_id'],
            'token': token,
            'expiry': token_expiry,
            'is_active': True
        }
        auth_collection.insert_one(auth_record)

        # Send OTP via sendChamp
        phone_number = user['phoneNumber']
        first_name = user['firstName']
        reference, otp = send_champ_otp(phone_number, first_name)

        users_collection.update_one({'_id': user['_id']}, {'$set': {'otp': otp, 'otp_reference': reference}})

        return jsonify({'message': 'Login successful', 'token': token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
    
# Endpoint to verify OTP and generate login token
@routes_authentication.route('/verify-otp', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'otp': {'type': 'string'}
                },
                'required': ['email', 'otp']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful',
            'examples': {
                'application/json': {
                    'message': 'Login successful',
                    'token': 'generated-token'
                }
            }
        },
        400: {
            'description': 'Invalid OTP',
            'examples': {
                'application/json': {
                    'message': 'Invalid OTP'
                }
            }
        }
    }
})
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    user = users_collection.find_one({'email': email})
    
    if user and user.get('otp') == otp:
        # Generate token and store in auth collection
        token = generate_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
        auth_record = {
            'user_id': user['_id'],
            'token': token,
            'expiry': token_expiry,
            'is_active': True
        }
        auth_collection.insert_one(auth_record)
        
        # Clear the OTP from the user's record
        users_collection.update_one({'_id': user['_id']}, {'$unset': {'otp': '', 'otp_reference': '', 'last_otp':otp}})
        return jsonify({'message': 'Login successful', 'token': token}), 200
    else:
        return jsonify({'message': 'Invalid OTP'}), 400
    

# Endpoint for user logout
@routes_authentication.route('/logout', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token'
        }
    ],
    'responses': {
        200: {
            'description': 'Logout successful',
            'examples': {
                'application/json': {
                    'message': 'Logout successful'
                }
            }
        },
        400: {
            'description': 'Invalid or expired token',
            'examples': {
                'application/json': {
                    'message': 'Invalid or expired token'
                }
            }
        }
    }
})
def logout():
    token = request.headers.get('Authorization')

    auth_record = auth_collection.find_one({'token': token, 'is_active': True})
    if auth_record:
        auth_collection.update_one({'_id': auth_record['_id']}, {'$set': {'is_active': False}})
        return jsonify({'message': 'Logout successful'}), 200
    else:
        return jsonify({'message': 'Invalid or expired token'}), 400