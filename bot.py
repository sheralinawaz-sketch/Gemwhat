import ssl
import json
import urllib.request
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

GEMINI_API_KEY = "AQ.Ab8RN6ILJ3iCPgnJkf2Cvi99VjUj5p7RqXsqMap6XHH_Er0xkQ"
PHONE_NUMBER_ID = "1537824876081909"
WHATSAPP_TOKEN = "EAAVZAAkizhm0BTPbkEnlZB7m18a2g9IzQXxMCJXdl4XHQXxbWfACqpIPhcnt43bbZCq4ZBljgwgxkd1uDEZC9F6ljuqEibLsuk60fswByx7u9ZC1wFOBpNccZCsp5L1TMXZABonazwVMO1st4HfbAP1rUrKnINt8vLn9CDSUVe3OZB9wPMbuZC3jOxSfZATwomKH8Qx0Ta8RO4dqns3M3R4eZB6qd1xd3Ec0IKKFhiWQ2RecUAKh4k4vDm054AORFC1RF1LlnlQkAX7i9zt94R2HtvUt4yJ3"
VERIFY_TOKEN = "sherali_secure_token"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_whatsapp_message(to_number, message_body):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": message_body}
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.read()}")
    except Exception as e:
        print(f"Error sending message: {e}")
    return None

@app.route("/", methods=["GET"])
def home():
    return "Bot is running perfectly!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            entry = data["entry"][0]
            change = entry["changes"][0]
            value = change["value"]
            if "messages" in value:
                message = value["messages"][0]
                sender_phone = message["from"]
                user_text = message["text"]["body"]
                
                response = model.generate_content(user_text)
                bot_reply = response.text
                
                send_whatsapp_message(sender_phone, bot_reply)
        except (KeyError, IndexError):
            pass
        return json.dumps({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
