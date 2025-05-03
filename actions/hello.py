from linebot.v3.messaging import ApiClient, MessagingApi

from main import get_configuration

def match(message: str) -> bool:
    return message.startswith("こんにちは")

def action(sender_id: str, message: str):
    profile = None
    with ApiClient(get_configuration()) as api_client:
        messaging_api = MessagingApi(api_client)
        profile = messaging_api.get_profile(sender_id)

    return "こんにちは、" + profile.display_name + "さん！"
