from flask import Blueprint, jsonify, request
from config import db
from flasgger import swag_from
import json, os
from cryptography.fernet import Fernet

routes_general_data = Blueprint('general_data', __name__)

political_parties_collection = db['political_parties']

# Encryption key (should be kept secure and consistent)
encryption_key = os.getenv('ENCRYPTION_KEY_VOTER_DATA')
encryption_key = encryption_key.encode()
cipher_suite = Fernet(encryption_key)

@routes_general_data.route('/general/political-parties', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'All Political Parties',
            'examples': {
                'application/json': {
                    'message': 'All Political Parties',
                    'political_parties': [
                        {
                            'name': 'Party Name',
                            'acronymn': 'Party Acronymn',
                        }
                    ],
                }
            }
        },
    }
})
def get_political_parties():
    political_parties = list(political_parties_collection.find(
        projection={'_id': False}))

    if len(list(political_parties)) == 0:
        # upload the political parties data to the database
        with open('data/political_parties.json') as f:
            data = json.load(f)
            political_parties_collection.insert_many(data)

        political_parties = list(political_parties_collection.find(projection={'_id': False}))
        return jsonify({"political_parties": list(political_parties)})
    
    return jsonify({"political_parties": list(political_parties)})


@routes_general_data.route('/voters_data', methods=['GET'])
@swag_from('swagger_docs/swagger_config.yml')
def get_voters():
    polling_unit = request.args.get('polling_unit')
    ward = request.args.get('ward')
    lga = request.args.get('lga')

    # Fetch data from MongoDB
    query = {
        "polling_unit": polling_unit,
        "ward": ward,
        "lga": lga
    }
    results = list(db.voters.find(query, {"_id": 0}))  # Exclude the MongoDB _id field

    # Convert results to JSON string and then encrypt
    results_json = json.dumps(results)
    encrypted_results = cipher_suite.encrypt(results_json.encode())

    # Return encrypted data as a response
    return jsonify({"data": encrypted_results.decode()})