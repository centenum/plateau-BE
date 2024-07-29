import os
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()  # This loads environment variables from .env file

client = MongoClient( os.environ.get('DATABASE_URI') )
db = client['plateau']

SENDCHAMP_PUBLIC_KEY = os.environ.get('SENDCHAMP_PUBLIC_KEY')