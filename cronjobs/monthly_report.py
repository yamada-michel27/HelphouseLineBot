from datetime import date, datetime, timedelta, timezone
import os
from linebot.v3.messaging import (
    ApiClient, MessagingApi,
    TextMessage, PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session, func, select
from app.models import GarbageLog, Group
from utils.db import engine
from main import configuration

def run():
    # 明日の日付を作って、月が変わっていれば今日が末日
    if os.getenv("DEBUG", "false").lower() != "true":
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
                    text=build_ranking_text(api_client, group_id),
                )]

                line_api.push_message_with_http_info(
                    PushMessageRequest(
                        to=group_id,
                        messages=messages
                    )
                )

def build_ranking_text(api_client: ApiClient, group_id: str) -> str:
    # 今月の開始日を取得
    now = datetime.now(timezone.utc)
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    with Session(engine) as session:
        # 今月のゴミ出しをグループ内で集計
        statement = (
            select(GarbageLog.user_id, func.count().label("count"))
            .where(
                GarbageLog.group_id == group_id,
                GarbageLog.created_at >= first_day_of_month
            )
            .group_by(GarbageLog.user_id)
            .order_by(func.count().desc())
        )

        results = session.exec(statement).all()

    if not results:
        return "今月はまだ誰もゴミを出していません。"

    # LINEのMessaging APIクライアントを初期化
    messaging_api = MessagingApi(api_client)

    # ユーザーIDから表示名を取得してマッピング
    display_names = {}
    for user_id, _ in results:
        try:
            profile = messaging_api.get_group_member_profile(group_id, user_id)
            display_names[user_id] = profile.display_name
        except Exception:
            display_names[user_id] = "(名前取得失敗)"

    # ランキングメッセージを作成
    lines = ["🏆 今月のゴミ出しランキング 🗑"]
    for i, (user_id, count) in enumerate(results, start=1):
        name = display_names.get(user_id, user_id)
        lines.append(f"{i}位: {name}（{count}回）")

    return "\n".join(lines)
