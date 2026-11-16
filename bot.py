import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# آپ کی فراہم کردہ اسناد (Credentials)
GEMINI_API_KEY = "AQ.Ab8RN6ILJ3iCPgnJkf2Cvi99VjUj5p7RqXsqMap6XHH_Er0xkQ"
PHONE_NUMBER_ID = "1537824876081909"
WHATSAPP_TOKEN = "EAAVZAAkizhm0BTPbkEnlZB7m18a2g9IzQXxMCJXdl4XHQXxbWfACqpIPhcnt43bbZCq4ZBljgwgxkd1uDEZC9F6ljuqEibLsuk60fswByx7u9ZC1wFOBpNccZCsp5L1TMXZABonazwVMO1st4HfbAP1rUrKnINt8vLn9CDSUVe3OZB9wPMbuZC3jOxSfZATwomKH8Qx0Ta8RO4dqns3M3R4eZB6qd1xd3Ec0IKKFhiWQ2RecUAKh4k4vDm054AORFC1RF1LlnlQkAX7i9zt94R2HtvUt4yJ3"

# فیس بک ڈیش بورڈ پر ویب ہک سیٹ اپ کے لیے وریفکیشن ٹوکن 
VERIFY_TOKEN = "sherali_secure_token" 

# جیمنائی کی سیٹنگ
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_whatsapp_message(to_number, text_message):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text_message}
    }
    requests.post(url, headers=headers, json=data)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Meta کی طرف سے Webhook کی تصدیق کے لیے
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Verification failed', 403

    # کسٹمر کا میسج موصول ہونے پر
    elif request.method == 'POST':
        body = request.get_json()
        if body.get('object'):
            try:
                entry = body['entry'][0]
                changes = entry['changes'][0]
                value = changes['value']
                
                # چیک کریں کہ آیا کوئی نیا میسج آیا ہے
                if 'messages' in value:
                    message = value['messages'][0]
                    sender_phone = message['from']
                    msg_text = message['text']['body']

                    # جیمنائی سے جواب تیار کروانا
                    response = model.generate_content(msg_text)
                    reply_text = response.text

                    # جواب واپس واٹس ایپ پر بھیجنا
                    send_whatsapp_message(sender_phone, reply_text)
            except Exception as e:
                print(f"Error: {e}")
                
            return jsonify({"status": "success"}), 200
        else:
            return 'Event not supported', 404

if __name__ == '__main__':
    # ٹرمکس میں پورٹ 5000 پر لوکل سرور چلانا
    app.run(host='0.0.0.0', port=5000)

