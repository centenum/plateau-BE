from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from PIL import Image
import io, os, base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Set up your OpenAI API key
openai_client = OpenAI(
    # This is the default and can be omitted
    api_key= os.getenv("OPENAI_KEY"),
)
THIS_MODEL = "gpt-4o-mini"

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/')
def home():
    return render_template('index.html')

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
                        {"type": "text", "text": "Extract in json format the VIN, DOB and full name if it's a Voter's card. If not, just say \"No Voter ID\". Please just the json itself, no markdown or newlines or escape characters"},
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
    
    file_path = os.path.join('uploads', 'captured_image.png')
    with open(file_path, 'wb') as f:
        f.write(image_data)

    return jsonify({"message": "Image uploaded successfully!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
