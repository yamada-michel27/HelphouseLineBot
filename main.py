import importlib
import os
import logging
import pkgutil
import certifi
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from actions.hello import action

# ログ設定
logger = logging.getLogger(__name__)

# .env 読み込み
load_dotenv()

# FastAPI インスタンス生成
app = FastAPI()

# LINE SDK インスタンス生成
configuration = Configuration(
    access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"),
    ssl_ca_cert=certifi.where()
)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# コールバックハンドリング
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body      = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"status": "ok"}

# メッセージイベントのハンドラ
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    cmd = event.message.text.strip()

    # ./actions ディレクトリにあるアクションをインポート
    if cmd == "こんにちは":
        reply = "こんにちは！"
    elif cmd == "やあ":
        reply = "やあ！"
    else:
        reply = f"{cmd}なんですね。"


    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("LINE Botを起動しています...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
