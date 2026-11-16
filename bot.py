import os
import json
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_whatsapp_message(recipient_phone, message_body):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": message_body}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.get_json()
        if data and 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages' and 'value' in change:
                        value = change['value']
                        if 'messages' in value:
                            for msg in value['messages']:
                                sender_phone = msg.get('from')
                                message_text = msg.get('text', {}).get('body')
                                
                                if message_text and sender_phone:
                                    try:
                                        response = model.generate_content(message_text)
                                        reply_text = response.text
                                    except Exception as e:
                                        print(f"Gemini Error: {e}")
                                        reply_text = "Sorry, I encountered an error processing your request."
                                    
                                    send_whatsapp_message(sender_phone, reply_text)
                                    
        return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(port=5000)
