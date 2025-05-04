from datetime import date, timedelta
import os
from linebot.v3.messaging import (
    ApiClient, MessagingApi,
    TextMessage, PushMessageRequest
)
from sqlmodel import Session, select
from app.models import Group
from utils.db import engine
from main import configuration

def run():
    # 明日の日付を作って、月が変わっていれば今日が末日
    if os.getenv("DEBUG", "false").lower() == "true":
        today = date.today()
        if (today + timedelta(days=1)).month == today.month:
            return

    print("月末の処理を実行します")
    
    with Session(engine) as session:
        # Botが参加しているすべてのグループIDを取得
        statement = select(Group.id)
        results = session.exec(statement).all()
        group_ids: list[int] = results
        
        with ApiClient(configuration) as api_client:
            line_api = MessagingApi(api_client)

            # 各グループにメッセージを送信
            for group_id in group_ids:
                messages = [TextMessage(
                    text="[ゴミ出し]\n"
                    "１番多く出したのは、○○さんでした！\n"
                    "\n"
                    "来月も人のことを思い行動しましょう！"
                )]

                line_api.push_message_with_http_info(
                    PushMessageRequest(
                        to=group_id,
                        messages=messages
                    )
                )
