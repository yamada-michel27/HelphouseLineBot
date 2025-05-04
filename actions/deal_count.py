from linebot.v3.messaging import ApiClient
from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session, select
from utils.db import engine

from app.models import User, GarbageLog, Group
import uuid

def match(event: MessageEvent, message: str) -> bool:
    return message in ["ゴミ", "trash"]

def action(event: MessageEvent, api_client: ApiClient, message: str): # api_clientいる？
    user_id = event.source.user_id

    # group_id が存在するか確認（グループトークのみ）
    if not (hasattr(event.source, "group_id") and event.source.group_id):
        return "この操作はグループ内でのみ実行できます。"

    group_id = event.source.group_id

    with Session(engine) as session:
        # ユーザー・グループが存在しない場合は新規で追加
        if not session.get(User, user_id):
            session.add(User(id=user_id))
        if not session.get(Group, group_id):
            session.add(Group(id=group_id))
        session.commit()

        # GarbageLogを追加
        log = GarbageLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            group_id=group_id,
            created_at=None,  # 自動で現在時刻が入る
        )
        session.add(log)
        session.commit()

        # ユーザーのゴミ捨て回数を取得
        count = session.exec(
            select(GarbageLog).where(
                GarbageLog.user_id == user_id,
                GarbageLog.group_id == group_id,
            )
        )
        count = len(list(count))

        return f"{count}回目のゴミ捨てですね！" if count > 0 else "初めてのゴミ捨てですね！"