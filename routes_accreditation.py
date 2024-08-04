import json
from flask import Blueprint, request, jsonify
from config import db
import uuid
from datetime import datetime, timezone
from flasgger import swag_from

routes_accreditation = Blueprint('accreditation_routes', __name__)

accreditation_collection = db.accreditation
voter_collection = db.voters

# Helper function to generate a unique session ID
def generate_session_id():
    return str(uuid.uuid4())


# Auto Accreditation: 3 steps
@routes_accreditation.route('/auto-accreditation/start', methods=['POST'])
@swag_from({
    'responses': {
        201: {
            'description': 'Auto accreditation started',
            'examples': {
                'application/json': {
                    'message': 'Auto accreditation started',
                    'sessionId': 'unique-session-id'
                }
            }
        }
    }
})
def start_auto_accreditation():
    session_id = generate_session_id()
    accreditation_collection.insert_one({
        'sessionId': session_id,
        'step': 1,
        'status': 'in-progress',
        'createdAt': datetime.now(timezone.utc)
    })
    return jsonify({'message': 'Auto accreditation started', 'sessionId': session_id}), 201

@routes_accreditation.route('/auto-accreditation/step1', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'sessionId',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Session ID'
        },
        {
            'name': 'voterCardImage',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Voter Card Image'
        }
    ],
    'responses': {
        200: {
            'description': 'Voter\'s card verified, proceed to face verification',
            'examples': {
                'application/json': {
                    'message': 'Voter\'s card verified, proceed to face verification',
                    'sessionId': 'unique-session-id'
                }
            }
        }
    }
})
def auto_accreditation_step1():
    data = request.get_json()
    session_id = data.get('sessionId')
    voter_card_image = data.get('voterCardImage')
    
    # Verify voter's card image logic here
    
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'voterCardImage': voter_card_image, 'step': 2}})
    return jsonify({'message': 'Voter\'s card verified, proceed to face verification', 'sessionId': session_id}), 200

@routes_accreditation.route('/auto-accreditation/step2', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'sessionId',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Session ID'
        },
        {
            'name': 'faceCaptureImage',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Face Capture Image'
        }
    ],
    'responses': {
        200: {
            'description': 'Face verified, proceed to polling unit verification',
            'examples': {
                'application/json': {
                    'message': 'Face verified, proceed to polling unit verification',
                    'sessionId': 'unique-session-id'
                }
            }
        }
    }
})
def auto_accreditation_step2():
    data = request.get_json()
    session_id = data.get('sessionId')
    face_capture_image = data.get('faceCaptureImage')
    
    # Verify face capture matches voter's card logic here
    
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'faceCaptureImage': face_capture_image, 'step': 3}})
    return jsonify({'message': 'Face verified, proceed to polling unit verification', 'sessionId': session_id}), 200

@routes_accreditation.route('/auto-accreditation/step3', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'sessionId',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Session ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Voter accredited successfully',
            'examples': {
                'application/json': {
                    'message': 'Voter accredited successfully',
                    'sessionId': 'unique-session-id'
                }
            }
        }
    }
})
def auto_accreditation_step3():
    data = request.get_json()
    session_id = data.get('sessionId')
    
    # Verify polling unit logic here
    
    # Retrieve voter details from previous steps
    accreditation_record = accreditation_collection.find_one({'sessionId': session_id})
    voter_details = {
        'voterCardImage': accreditation_record.get('voterCardImage'),
        'faceCaptureImage': accreditation_record.get('faceCaptureImage'),
        'accreditedAt': datetime.now(timezone.utc)
    }
    
    # Update the record to complete accreditation
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'status': 'completed', 'voterDetails': voter_details}})
    return jsonify({'message': 'Voter accredited successfully', 'sessionId': session_id}), 200

# Manual Accreditation: 2 steps
@routes_accreditation.route('/manual-accreditation/step1', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'vin',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Voter Identification Number (VIN)'
        }
    ],
    'responses': {
        200: {
            'description': 'VIN valid',
            'examples': {
                'application/json': {
                    'message': 'VIN valid',
                    'voterDetails': {
                        'firstName': 'John',
                        'lastName': 'Doe',
                        'pollingUnit': 'Unit 1'
                    }
                }
            }
        },
        400: {
            'description': 'Invalid VIN',
            'examples': {
                'application/json': {
                    'message': 'Invalid VIN'
                }
            }
        }
    }
})
def manual_accreditation_step1():
    data = request.get_json()
    vin = data.get('vin')

    # Verify VIN logic here
    # For demonstration, let's assume VIN validation is done through a mock function
    voter = verify_vin(vin)
    if voter:
        return jsonify({'message': 'VIN valid', 'voterDetails': voter}), 200
    else:
        return jsonify({'message': 'Invalid VIN'}), 400

def verify_vin(vin):
    # Mock function to verify VIN
    # In real implementation, replace with actual VIN verification logic
    # For example, a database lookup
    voters = list(voter_collection.find())
    if len(voters) == 0:
        # Upload the voters data to the database
        with open('data/voters.json') as f:
            data = json.load(f)
            voter_collection.insert_many(data)
        
    voter = voter_collection.find_one({'vin': vin })
    return voter

@routes_accreditation.route('/manual-accreditation/step2', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'vin',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Voter Identification Number (VIN)'
        },
        {
            'name': 'voterCardImage',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Voter Card Image'
        },
        {
            'name': 'faceCaptureImage',
            'in': 'body',
            'type': 'string',
            'required': True,
            'description': 'Face Capture Image'
        }
    ],
    'responses': {
        201: {
            'description': 'Voter accredited successfully',
            'examples': {
                'application/json': {
                    'message': 'Voter accredited successfully'
                }
            }
        }
    }
})
def manual_accreditation_step2():
    data = request.get_json()
    vin = data.get('vin')
    voter_card_image = data.get('voterCardImage')
    face_capture_image = data.get('faceCaptureImage')

    # Save the voter's face and card images
    voter_details = {
        'vin': vin,
        'voterCardImage': voter_card_image,
        'faceCaptureImage': face_capture_image,
        'accreditedAt': datetime.now(timezone.utc)
    }
    
    accreditation_collection.insert_one({
        'status': 'completed',
        'voterDetails': voter_details
    })
    return jsonify({'message': 'Voter accredited successfully'}), 201