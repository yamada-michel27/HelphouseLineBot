def match(message: str) -> bool:
    return message == "@id"

def action(sender_id: str, message: str):
    return "こんにちは、あなたのIDは" + sender_id + "です！"
