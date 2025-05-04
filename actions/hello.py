from linebot.v3.messaging import ApiClient, MessagingApi, ImageMessage
from linebot.v3.webhooks import MessageEvent
# プロフィールを取得するサンプル

def match(event: MessageEvent, message: str) -> bool:
    return message.startswith("こんにちは")

# event: 受信したメッセージの情報
# （詳細: https://developers.line.biz/ja/reference/messaging-api/#message-event）
# api_client: LINE APIを操作するためのクライアント
# message: 受信したメッセージの内容（event.message.text）
def action(event: MessageEvent, api_client: ApiClient, message: str):
    messaging_api = MessagingApi(api_client)
    profile = messaging_api.get_profile(event.source.user_id)

    return [
        "こんにちは、" + profile.display_name + "さん！",
        # ImageMessage: https://developers.line.biz/ja/reference/messaging-api/#image-message
        ImageMessage(
            original_content_url=profile.picture_url,
            preview_image_url=profile.picture_url,
        ),
    ]
