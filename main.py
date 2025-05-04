import importlib
import os
import logging
import pkgutil
import certifi
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models.message import Message
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import actions

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

def get_configuration():
    return configuration

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
    message = event.message.text.strip()

    # ./actions ディレクトリにあるアクションをインポート
    for _, module_name, _ in pkgutil.iter_modules(actions.__path__):
        module = importlib.import_module(f"actions.{module_name}")
        if hasattr(module, "match") and hasattr(module, "action"):
            if module.match(event, message):
                with ApiClient(configuration) as api_client:
                    # 該当するアクションファイルのaction関数を実行
                    messages = []
                    replies = module.action(event, api_client, message)

                    if not isinstance(replies, list):
                        replies = [replies]

                    # replyが文字列の場合はTextMessageに変換
                    for i, reply in enumerate(replies):
                        if isinstance(reply, str):
                            messages.append(TextMessage(text=reply))
                        elif isinstance(reply, Message):
                            messages.append(reply)

                    if len(messages) > 0:
                        line_api = MessagingApi(api_client)
                        line_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=messages
                            )
                        )
                return

if __name__ == "__main__":
    import uvicorn
    logger.info("LINE Botを起動しています...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
