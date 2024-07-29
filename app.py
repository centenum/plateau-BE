from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import os, base64
from openai import OpenAI
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, jwt_optional, get_jwt_identity

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')

jwt = JWTManager(app)

# OpenAI setup
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai_client = OpenAI(api_key=OPENAI_KEY)
THIS_MODEL = "gpt-4o-mini"

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    is_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    user = db.relationship('User', backref=db.backref('voters', lazy=True))

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Functions
def answer_based_on_election_info(user_chat):
    response = openai_client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a cool chat bot"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{ELECTION_INFO}\n\nPlease use the information above to answer the user chat as concise as possible. User chat: {user_chat}.\n\nIf the user chat is not related to the election info, just return a sentence letting the user know you don't have an answer."},
                ]
            }
        ],
        max_tokens=300
    )

    result = response.choices[0].message.content
    return result

def translate_text_to_hausa(input_text):
    response = openai_client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a cool chat bot."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Translate {input_text} to Hausa. Just return the hausa translation."},
                ]
            }
        ],
        max_tokens=300
    )

    result = response.choices[0].message.content
    return result

def decode_image_to_ocr(base64_image):
    response = openai_client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a cool image analyst required for OCR."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract in json format the VIN, DOB and full name if it's a Voter's card. If not, just say \"No Voter ID\". Please just the json itself, no markdown or newlines or escape characters"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=300
    )

    description = response.choices[0].message.content
    return description

# Routes
@app.route('/')
def home():
    return "Hello world 👋"

@app.route('/about')
def about():
    return 'This is the about page.'

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/verify_user/<int:user_id>', methods=['POST'])
@jwt_required()
def verify_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403

    user = User.query.get(user_id)
    if user:
        user.is_verified = True
        db.session.commit()
        return jsonify({"message": "User verified successfully"}), 200

    return jsonify({"error": "User not found"}), 404

@app.route('/voter_input', methods=['POST'])
@jwt_required()
def voter_input():
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    address = data.get('address')
    date_of_birth = data.get('date_of_birth')
    contact = data.get('contact')
    
    if not all([user_id, name, address, date_of_birth]):
        return jsonify({"error": "User ID, name, address, and date of birth are required"}), 400
    
    user = User.query.get(user_id)
    if user:
        voter = Voter(user_id=user_id, name=name, address=address, date_of_birth=date_of_birth, contact=contact)
        db.session.add(voter)
        db.session.commit()
        return jsonify({"message": "Voter data saved successfully"}), 200
    
    return jsonify({"error": "User not found"}), 404

@app.route('/voters_card_ocr', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        base64_image = encode_image(file.stream)

        response = openai_client.chat.completions.create(
            model=THIS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cool image analyst required for OCR."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract in json format the VIN, DOB and fullname if it's a Voter's card. If not, just return {'status': False}. Please just the json itself, no markdown or newlines or escape characters"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )

        description = response.choices[0].message.content

        return jsonify({"description": description})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    image_data = data['image']
    image_data = image_data.split(",")[1]  # Remove the data URL prefix
    image_data = base64.b64decode(image_data)

    base64_image = base64.b64encode(image_data).decode('utf-8')
    result = decode_image_to_ocr(base64_image)
    print("Result:", result, type(result))
    try:
        result = dict(eval(result))
        result["status"] = True
        print("Worked:", result, type(result))
    except Exception as e:
        print("Error:", e)
        result = {"status": False}
    
    file_path = os.path.join('uploads', 'captured_image.png')
    with open(file_path, 'wb') as f:
        f.write(image_data)

    return jsonify({"message": "Image uploaded successfully!", "data": result}), 200

@app.route('/whatsapp_webhook', methods=['POST'])
def whatsapp_webhook():
    print('whatsapp_webhook:', request.get_data())
    incoming_msg = request.values.get('Body', '').strip()
    senderId = request.values.get('From', '').strip()

    response_message = answer_based_on_election_info(incoming_msg)
    send_whatsapp_message(response_message, recipient=senderId)

    return jsonify({"success": True}), 200

@app.route('/translate_to_hausa', methods=['POST'])
def translate_to_hausa():
    data = request.get_json()
    input_text = data.get('text')

    response = translate_text_to_hausa(input_text)

    return jsonify({"text": response})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
"""
User Schema collection
id: Integer, Primary Key
username: String(150), Unique, Not Null
password_hash: String(150), Not Null
role: String(50), Default 'user'
is_verified: Boolean, Default False

User registration 
User login

Voter Schema collection
id: Integer, Primary Key
user_id: Integer, Foreign Key (references User.id), Not Null
name: String(150), Not Null
address: String(250), Not Null
date_of_birth: Date, Not Null
contact: String(100), Optional

Voter input is the data - data = request.get_json()
user_id = data.get('user_id')
name = data.get('name')
address = data.get('address')
date_of_birth = data.get('date_of_birth')
contact = data.get('contact')
polling_unit = data.get('polling_unit')

verify_voter is the data -  data = request.get_json()
    voter_id = data.get('voter_id')
    user_id = data.get('user_id')
   

"""