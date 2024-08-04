from flask.json.provider import DefaultJSONProvider
from bson import json_util, ObjectId
from datetime import datetime

class MongoJsonEncoder(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)