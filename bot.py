import os
import json
import urllib.request
import ssl
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

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
    data = json.dumps({
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": message_body}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx) as response:
            return response.read()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403
    
    if request.method == "POST":
        data = request.get_json()
        try:
            if "entry" in data and data["entry"]:
                entry = data["entry"][0]
                if "changes" in entry and entry["changes"]:
                    value = entry["changes"][0]["value"]
                    if "messages" in value and value["messages"]:
                        message = value["messages"][0]
                        sender_phone = message["from"]
                        user_text = message["text"]["body"]
                        
                        response = model.generate_content(user_text)
                        bot_reply = response.text
                        
                        send_whatsapp_message(sender_phone, bot_reply)
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return "OK", 200
        return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

