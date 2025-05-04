from linebot.v3.messaging import ApiClient
from linebot.v3.webhooks import MessageEvent
from sqlmodel import Session
from utils.db import engine

from app.models import SampleCount
# カウントサンプル

def match(event: MessageEvent, message: str) -> bool:
    return message == "カウント"

def action(event: MessageEvent, api_client: ApiClient, message: str):
    user_id = event.source.user_id

    with Session(engine) as session:
        # ユーザーのゴミ捨て回数をカウント
        record = session.get(SampleCount, user_id)
        if record is None:
            record = SampleCount(user_id=user_id, count=1)
            session.add(record)
        else:
            record.count += 1
        session.commit()
        session.refresh(record)

        return f"{record.count}回目のゴミ捨てですね！"
