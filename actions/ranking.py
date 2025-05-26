from datetime import datetime, timezone
from linebot.v3.messaging import ApiClient, MessagingApi
from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session, select, func
from utils.db import engine
from app.models import TaskLog, TaskType

DEFAULT_NAME = "(名無しさん)"


def match(event: MessageEvent, message: str) -> bool:
    return message.strip() == "@ranking"


def action(event: MessageEvent, api_client: ApiClient, message: str) -> str:
    if not hasattr(event.source, "group_id") or not event.source.group_id:
        return "このコマンドは個人チャットでは使用できません。"
    
    # 今月の開始日を取得
    now = datetime.now(timezone.utc)
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    group_id = event.source.group_id

    with Session(engine) as session:
        # 今月のゴミ出しをグループ内で集計
        statement = (
            select(TaskLog.user_id, func.count().label("count"))
            .where(
                TaskLog.group_id == group_id,
                TaskLog.created_at >= first_day_of_month,
                TaskLog.task_type == TaskType.GARBAGE
            )
            .group_by(TaskLog.user_id)
            .order_by(func.count().desc())
        )

        results = session.exec(statement).all()

    if not results:
        return "今月はまだ誰もゴミを出していません。"

    # LINEのMessaging APIクライアントを初期化
    messaging_api = MessagingApi(api_client)

    # ユーザーIDから表示名を取得してマッピング
    display_names = {}
    any_name_failed = False

    for user_id, _ in results:
        try:
            profile = messaging_api.get_group_member_profile(group_id, user_id)
            display_names[user_id] = profile.display_name
        except Exception:
            display_names[user_id] = DEFAULT_NAME
            any_name_failed = True

    # ランキングメッセージを作成
    lines = ["🏆 今月のゴミ出しランキング 🗑",
             "(Garbage disposal ranking this month)"
             ]
    prev_count = None
    display_rank = 1

    for i, (user_id, count) in enumerate(results, start=1):
        name = display_names.get(user_id, user_id)

        if count != prev_count:
            display_rank = i
            prev_count = count
        lines.append(f"{display_rank}位: {name}（{count}回）")
        
        
    if any_name_failed:
        lines.append("\n※名前が表示されていない方は、LINE Botを友だち追加すると表示されます。")

    return "\n".join(lines)
