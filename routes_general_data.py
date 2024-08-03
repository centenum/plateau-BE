from flask import Blueprint, jsonify
from config import db
from flasgger import swag_from
import json

routes_general_data = Blueprint('general_data', __name__)

political_parties_collection = db['political_parties']

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