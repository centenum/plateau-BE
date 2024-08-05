import os

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()  # This loads environment variables from .env file

OPENAI_KEY = os.getenv("OPENAI_KEY")

# Set up your OpenAI API key
openai_client = OpenAI(
    # This is the default and can be omitted
    api_key= os.getenv("OPENAI_KEY"),
)
THIS_MODEL = "gpt-4o-mini"

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