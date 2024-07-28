from twilio.rest import Client
import os

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)



def send_whatsapp_message(message):
    result = client.messages.create(
    from_='whatsapp:+14155238886',
    body=message,
    to='whatsapp:+2348136694562'
    )
    return result

# message = send_whatsapp_message("Hello")
# print(message.sid)