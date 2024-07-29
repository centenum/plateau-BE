from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from PIL import Image
import io, os, base64
from flask_cors import CORS
from whatsapp_bot import send_whatsapp_message

from routes_accreditation import accreditation_routes
from routes_authentication import authentication_routes

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
swagger = Swagger(app)

app.register_blueprint(accreditation_routes)
app.register_blueprint(authentication_routes)

OPENAI_KEY = os.getenv("OPENAI_KEY")

# Set up your OpenAI API key
openai_client = OpenAI(
    # This is the default and can be omitted
    api_key= os.getenv("OPENAI_KEY"),
)
THIS_MODEL = "gpt-4o-mini"

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')


# Read the .txt file content
ELECTION_INFO = ""
with open('LLM_election_info.txt', 'r') as file:
    ELECTION_INFO = file.read()

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


# Function to translate input_text to hausa:
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
    # Send the request to the OpenAI API
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

    # Extract the description
    description = response.choices[0].message.content

    return description

@app.route('/')
def home():
    return "Hello world 👋"

@app.route('/about')
def about():
    return 'This is the about page.'


@app.route('/voters_card_ocr', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Encode the image file as base64
        base64_image = encode_image(file.stream)

        # Send the request to the OpenAI API
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

        # Extract the description
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

    # Encode the decoded image back to base64 for the OCR function
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

##### Twilio Whatsapp Webhook:
@app.route('/whatsapp_webhook', methods=['POST'])
def whatsapp_webhook():
    #print request.data
    print('whatsapp_webhook:', request.get_data())
    incoming_msg = request.values.get('Body', '').strip()
    senderId = request.values.get('From', '').strip()

    response_message = answer_based_on_election_info(incoming_msg)
    send_whatsapp_message(response_message, recipient=senderId)

    return jsonify({"success": True}), 200

##### Route to translate text to hausa:
@app.route('/translate_to_hausa', methods=['POST'])
def translate_to_hausa():
    data = request.get_json()
    input_text = data.get('text')

    response = translate_text_to_hausa(input_text)

    return jsonify({"text": response})

if __name__ == '__main__':
    app.run(debug=True)
