from flask import Blueprint, request, jsonify
from config import db, SENDCHAMP_PUBLIC_KEY

import string, random, uuid
from datetime import datetime, timedelta, timezone
import bcrypt, requests
from flasgger import swag_from

from decorators import validate_schema
from schema import GenerateChairmanWithDeputySchema

routes_authentication = Blueprint('authentication_routes', __name__)

users_collection = db.users
auth_collection = db.auth
chairman_collection = db.chairman
deputy_chairman_collection = db.deputy_chairman

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
    
def verify_sendchamp_otp(user, verification_code):
    verification_reference = user.get('otp_reference')  # Assuming this is stored in the user dict

    request_data = {
        'verification_code': verification_code,
        'verification_reference': verification_reference
    }
    request_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SENDCHAMP_PUBLIC_KEY}'
    }

    try:
        response = requests.post(
            'https://api.sendchamp.com/api/v1/verification/confirm',
            json=request_data,
            headers=request_headers
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as err:
        print(f"Error verifying OTP: {err}")
        return False



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
                    'username': {'type': 'string'},
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
                    'password': 'generated-password',
                    'hashedPassword': 'hashed-password'
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
    username = data.get('username')
    password = generate_password()
    created_at = datetime.now(timezone.utc)

    # Check if the username or email already exists
    if users_collection.count_documents({'$or': [{'username': username}, {'email': email}]}):
        return jsonify({'message': 'Username or email already exists'}), 400

    # Hash the password with bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': hashed_password,
        'createdAt': created_at,
        'role': role
    }

    users_collection.insert_one(user)
    return jsonify({'message': 'User registered successfully', 'password': password, 'hashedPassword': hashed_password}), 201

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
            'description': 'Login successful',
            'examples': {
                'application/json': {
                    'message': 'Login successful',
                    'token': 'generated-token',
                    'hashedPassword': 'password-hash',
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
    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'message': 'Invalid email or password'}), 401

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
    # phone_number = user.get('phoneNumber')
    # first_name = user['firstName']
    # reference, otp = send_champ_otp(phone_number, first_name)
    # users_collection.update_one({'_id': user['_id']}, {'$set': {'otp': otp, 'otp_reference': reference, 'lastLogin': datetime.now(timezone.utc)}})

    users_collection.update_one({'_id': user['_id']}, {'$set': {'lastLogin': datetime.now(timezone.utc)}})

    # Extract the hash and salt from the stored password
    hash_salt = user['password']  # Assuming the stored format includes the salt
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'hashedPassword': hash_salt,
    }), 200 
    
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
                    'username': {'type': 'string'},
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
    username = data.get('username')
    otp = data.get('otp')

    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'Invalid username'}), 400
    
    if not user.get('otp'):
        return jsonify({'message': 'OTP not sent'}), 400

    otp_verified =verify_sendchamp_otp(user, otp) # returns True or False
    
    if otp_verified:
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


@routes_authentication.route('/create-chairman', methods=['POST'])
@validate_schema(GenerateChairmanWithDeputySchema())
def create_chairman_with_deputy():
    data = request.get_json()
    chairman_data = data.get('chairman')
    deputy_data = data.get('deputyChairman')

    chairman_data['in_review'] = True
    deputy_data['in_review'] = True

    chairman_collection.insert_one(chairman_data)
    deputy_chairman_collection.insert_one(deputy_data)

    return jsonify({'message': 'Chairman created successfully', 'password': "password"}), 201


# Endpoint to get all chairmen
@routes_authentication.route('/chairmen', methods=['GET'])
def get_chairmen():
    chairmen = list(chairman_collection.find(projection={'_id': False}))
    return jsonify({"chairmen": chairmen}), 200


# Endpoint to get all deputy chairmen
@routes_authentication.route('/deputy-chairmen', methods=['GET'])
def get_deputy_chairmen():
    deputy_chairmen = list(deputy_chairman_collection.find(projection={'_id': False}))
    return jsonify({"deputy_chairmen": deputy_chairmen}), 200


@routes_authentication.route('/approve-chairman', methods=['POST'])
def approve_chairman():
    data = request.get_json()
    chairman_id = data.get('chairman_id')

    chairman_collection.update_one({'_id': chairman_id}, {'$set': {'in_review': False, 'approved': True}})
    return jsonify({'message': 'Chairman approved'}), 200


@routes_authentication.route('/approve-deputy-chairman', methods=['POST'])
def approve_deputy_chairman():
    data = request.get_json()
    deputy_chairman_id = data.get('deputy_chairman_id')

    deputy_chairman_collection.update_one({'_id': deputy_chairman_id}, {'$set': {'in_review': False, 'approved': True}})
    return jsonify({'message': 'Deputy Chairman approved'}), 200