from datetime import datetime, timezone
from linebot.v3.messaging import ApiClient
from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session, select, func
from utils.db import engine
from app.models import GarbageLog


def match(event: MessageEvent, message: str) -> bool:
    return message.strip() == "@ranking"


def action(event: MessageEvent, api_client: ApiClient, message: str) -> str:
    group_id = event.source.group_id
    if not group_id:
        return "このコマンドはグループ内でのみ使用できます。"

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

    # ランキングメッセージ
    lines = ["🏆🏆🏆 今月のゴミ出しランキング 🏆🏆🏆🏆"]
    for i, (user_id, count) in enumerate(results, start=1):
        lines.append(f"{i}位: {user_id}（{count}回）")

    return "\n".join(lines)