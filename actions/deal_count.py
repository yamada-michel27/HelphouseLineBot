from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session, select
from utils.db import engine

from app.models import User, TaskLog, Group, TaskType
import uuid

# ApiClientのインポート（適切な場所に合わせて修正してください）
from linebot.v3.messaging import ApiClient

class Config_Message:
    ADD_ME_MESSAGE = '''
        ユーザーIDを特定できませんでした。私を友だち追加してください。
        ----------------------------------------------------------
        I couldn't identify your user ID.Please add me as a friend.
    '''

MESSAGE_TO_TASK_TYPE = {
    "#tr": TaskType.GARBAGE,
    # "#dish": TaskType.DISHWASHING,
}

def match(event: MessageEvent, message: str) -> bool:
    return message.strip() in MESSAGE_TO_TASK_TYPE

def action(event: MessageEvent, api_client: ApiClient, message: str):
    user_id = event.source.user_id

    if not user_id:
        return Config_Message.ADD_ME_MESSAGE

    # group_id が存在するか確認（グループトークのみ）
    if not (hasattr(event.source, "group_id") and event.source.group_id):
        return "この操作はグループ内でのみ実行できます。"

    group_id = event.source.group_id

    task_type = MESSAGE_TO_TASK_TYPE[message.strip()]

    with Session(engine) as session:
        # ユーザー・グループが存在しない場合は新規で追加
        if not session.get(User, user_id):
            session.add(User(id=user_id))
        if not session.get(Group, group_id):
            session.add(Group(id=group_id))
        session.commit()

        # GarbageLogを追加
        log = TaskLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            group_id=group_id,
            task_type=task_type,
            created_at=None,  # 自動で現在時刻が入る
        )
        session.add(log)
        session.commit()

        # ユーザーのゴミ捨て回数を取得
        count = session.exec(
            select(TaskLog).where(
                TaskLog.user_id == user_id,
                TaskLog.group_id == group_id,
                TaskLog.task_type == task_type,
            )
        )
        count = len(list(count))


        return f"{count}回目のゴミ捨てですね！" if count > 1 else "初めてのゴミ捨てNice！"
