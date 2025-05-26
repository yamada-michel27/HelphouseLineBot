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
from linebot.v3.webhooks import MessageEvent, JoinEvent, TextMessageContent, MemberJoinedEvent
from sqlmodel import Session
from app.models import Group
from utils.db import engine

from fastapi.responses import Response

import actions
import cronjobs

DEFAULT_NAME = "(名無しさん)"

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

join_message = """こんにちは！
このボットは、毎月のゴミ出しのカウントを行います。
ゴミ出しをしたら「#tr」と送信してください。
毎月の最終日に、その月のランキングをお知らせします。

【コマンド】
「#tr」
→ゴミ出しのカウントをします
「@ranking」
→現時点でのランキングをお知らせします
-----------------
Hello!
This bot helps count how many times you've taken out the trash each month.
When you take out the trash, just send #tr.
At the end of each month, the bot will notify the group with the monthly ranking.

[Commands]
#tr
→ Records a trash-taking action.

@ranking
→ Shows the current trash-taking ranking.
"""


@handler.add(MemberJoinedEvent)
def handle_member_joined(event: MemberJoinedEvent):
    group_id = event.source.group_id
    joined_user_ids = [member.user_id for member in event.joined.members]
    
    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        messages = []
        
        for user_id in joined_user_ids:
            try:
                profile = line_api.get_group_member_profile(group_id, user_id)
                display_name = profile.display_name
            except Exception as e:
                logger.warning(f"ユーザー{user_id}の表示名取得に失敗しました:{e}")
                display_name = DEFAULT_NAME
                
            messages.append(
                TextMessage(
                    text=f"{display_name}さん、ようこそ！ \n{join_message}"
                )
            )
            
        if messages:
            line_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
            )
        )


@handler.add(JoinEvent)
def handle_join(event: JoinEvent):
    # グループに参加したときの処理
    logger.info(f"Joined group: {event.source.group_id}")

    # 参加したグループの情報をデータベースに保存
    with Session(engine) as session:
        record = session.get(Group, event.source.group_id)
        if record is None:
            record = Group(id=event.source.group_id)
            session.add(record)
            session.commit()
            session.refresh(record)
        logger.info(f"新しいグループがデータベースに保存されました: {event.source.group_id}")

    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=join_message)]
            )
        )


# メッセージイベントのハンドラ
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    message = event.message
    text = message.text

    # ./actions ディレクトリにあるアクションをインポート
    for _, module_name, _ in pkgutil.iter_modules(actions.__path__):
        module = importlib.import_module(f"actions.{module_name}")
        if hasattr(module, "match") and hasattr(module, "action"):
            if module.match(event, text):
                with ApiClient(configuration) as api_client:
                    # 該当するアクションファイルのaction関数を実行
                    messages = []
                    replies = module.action(event, api_client, text)

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


# Cronジョブの実行
@app.post("/cron")
def cron(request: Request):
    # CRON_TOKEN が必ず設定されていることを前提とする
    excepted_token = os.getenv("CRON_TOKEN")
    if not excepted_token:
        raise RuntimeError("CRON_TOKEN is not set in environment variables.")

    # Authorization ヘッダーのチェック
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    provided_token = auth_header.removeprefix("Bearer ").strip()
    if provided_token != os.getenv("CRON_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ./cronjobs ディレクトリにあるCronジョブをインポート
    for _, module_name, _ in pkgutil.iter_modules(cronjobs.__path__):
        module = importlib.import_module(f"cronjobs.{module_name}")
        if hasattr(module, "run"):
            try:
                module.run()
            except Exception as e:
                logger.error(f"Error in cron job {module_name}: {e}")
                return {"status": "error", "message": str(e)}

    return {"status": "ok"}

@app.get("/healthz", include_in_schema=False)
def health_check():
    return Response(content="ok", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    logger.info("LINE Botを起動しています...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)