from flask import Blueprint, request, jsonify
from config import db
import uuid
from datetime import datetime, timezone

routes_accreditation = Blueprint('accreditation_routes', __name__)

accreditation_collection = db.accreditation

# Helper function to generate a unique session ID
def generate_session_id():
    return str(uuid.uuid4())


# Auto Accreditation: 3 steps
@routes_accreditation.route('/auto-accreditation/start', methods=['POST'])
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
def auto_accreditation_step1():
    data = request.get_json()
    session_id = data.get('sessionId')
    voter_card_image = data.get('voterCardImage')
    
    # Verify voter's card image logic here
    
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'voterCardImage': voter_card_image, 'step': 2}})
    return jsonify({'message': 'Voter\'s card verified, proceed to face verification', 'sessionId': session_id}), 200

@routes_accreditation.route('/auto-accreditation/step2', methods=['POST'])
def auto_accreditation_step2():
    data = request.get_json()
    session_id = data.get('sessionId')
    face_capture_image = data.get('faceCaptureImage')
    
    # Verify face capture matches voter's card logic here
    
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'faceCaptureImage': face_capture_image, 'step': 3}})
    return jsonify({'message': 'Face verified, proceed to polling unit verification', 'sessionId': session_id}), 200

@routes_accreditation.route('/auto-accreditation/step3', methods=['POST'])
def auto_accreditation_step3():
    data = request.get_json()
    session_id = data.get('sessionId')
    polling_unit = data.get('pollingUnit')
    
    # Verify polling unit logic here
    
    # Retrieve voter details from previous steps
    accreditation_record = accreditation_collection.find_one({'sessionId': session_id})
    voter_details = {
        'voterCardImage': accreditation_record.get('voterCardImage'),
        'faceCaptureImage': accreditation_record.get('faceCaptureImage'),
        'pollingUnit': polling_unit,
        'accreditedAt': datetime.now(timezone.utc)
    }
    
    # Update the record to complete accreditation
    accreditation_collection.update_one({'sessionId': session_id}, {'$set': {'status': 'completed', 'voterDetails': voter_details}})
    return jsonify({'message': 'Voter accredited successfully', 'sessionId': session_id}), 200

# Manual Accreditation: 2 steps
@routes_accreditation.route('/manual-accreditation/step1', methods=['POST'])
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
    mock_voter = {
        'firstName': 'John',
        'lastName': 'Doe',
        'pollingUnit': 'Unit 1'
    }
    return mock_voter if vin == 'valid_vin' else None

@routes_accreditation.route('/manual-accreditation/step2', methods=['POST'])
def manual_accreditation_step2():
    data = request.get_json()