from twilio.rest import Client
import os

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)



def send_whatsapp_message():
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body='Welcome. I am your assistance to guide you for Elections in Plateau.',
    to='whatsapp:+2348136694562'
    )
    return message

message = send_whatsapp_message()
print(message.sid)