from flask import Flask, abort
from flask import request
import os
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage, AudioMessage, AudioSendMessage)
import librosa

# generate instance
app = Flask(__name__)

# get environmental value from heroku
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# endpoint
@app.route("/")
def test():
    return "<h1>It Works!</h1>"

# endpoint from linebot
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# handle message from LINE
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
    
@handler.add(MessageEvent, message=AudioMessage)
def handle_message(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    
    try:
        with open(f"/app/static/audio/{message_id}.m4a", 'wb') as fd:
            fd.write(message_content.content)
            
            original_content_url=f'https://mimic-chatbot-backend.herokuapp.com/static/audio/{message_id}.m4a'
            
            DEFAULT_FS = 22050
            x, fs = librosa.load(original_content_url, DEFAULT_FS)
            feature = librosa.feature.spectral_centroid(x, fs)
            
            message = ",".join(feature)
    except Exception as e:
        message = e
    
    
    # type_str = str(type(message_content))
    # type_content_str = str(type(message_content.content))
    # try:
    #     message_content_len = len(message_content.content)
    # except Exception as e:
    #     message_content_len = e
    
    line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="Yeah!!\n{message}"))        

if __name__ == "__main__":
	app.run()