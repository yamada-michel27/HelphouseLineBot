from linebot.v3.messaging import ApiClient
from linebot.v3.webhooks import MessageEvent
# ユーザー情報を取得するサンプル

def match(event: MessageEvent, message: str) -> bool:
    return message == "@id"

def action(event: MessageEvent, api_client: ApiClient, message: str):
    reply = "こんにちは、あなたのIDは" + event.source.user_id + "です！"

    if hasattr(event.source, "group_id") and event.source.group_id:
        reply += "\nグループIDは" + event.source.group_id + "です！"

    if hasattr(event.source, "group_id") and event.source.room_id:
        reply += "\nルームIDは" + event.source.room_id + "です！"

    return reply
