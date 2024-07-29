from flask import Blueprint, request, jsonify
from config import db

import string, random, uuid
from datetime import datetime, timedelta

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


# Endpoint to register users (APO or PO)
@routes_authentication.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    role = data.get('role', 'APO')  # Default role is APO if not specified
    password = generate_password()
    created_at = datetime.utcnow()

    user = {
        'firstName': first_name,
        'lastName': last_name,
        'password': password,
        'createdAt': created_at,
        'role': role
    }

    users_collection.insert_one(user)
    return jsonify({'message': 'User registered successfully', 'password': password}), 201

# Endpoint for user login
@routes_authentication.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    role = data.get('role')
    phone_number = data.get('phoneNumber')  # Assuming phone number is provided for OTP

    user = users_collection.find_one({'firstName': first_name, 'lastName': last_name, 'role': role})
    
    if user:
        otp = ''.join(random.choice(string.digits) for _ in range(6))
        sendChamp.send_sms(phone_number, otp)  # Send OTP via sendChamp

        users_collection.update_one({'_id': user['_id']}, {'$set': {'otp': otp}})
        return jsonify({'message': 'OTP sent successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404
    
# Endpoint to verify OTP and login
@routes_authentication.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    role = data.get('role')
    otp = data.get('otp')

    user = users_collection.find_one({'firstName': first_name, 'lastName': last_name, 'role': role})
    
    if user and user.get('otp') == otp:
        # Generate token and store in auth collection
        token = generate_token()
        token_expiry = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        auth_record = {
            'user_id': user['_id'],
            'token': token,
            'expiry': token_expiry,
            'is_active': True
        }
        auth_collection.insert_one(auth_record)
        
        # Clear the OTP from the user's record
        users_collection.update_one({'_id': user['_id']}, {'$unset': {'otp': ''}})
        return jsonify({'message': 'Login successful', 'token': token}), 200
    else:
        return jsonify({'message': 'Invalid OTP'}), 400
    

# Endpoint for user logout
@routes_authentication.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')

    auth_record = auth_collection.find_one({'token': token, 'is_active': True})
    if auth_record:
        auth_collection.update_one({'_id': auth_record['_id']}, {'$set': {'is_active': False}})
        return jsonify({'message': 'Logout successful'}), 200
    else:
        return jsonify({'message': 'Invalid or expired token'}), 400