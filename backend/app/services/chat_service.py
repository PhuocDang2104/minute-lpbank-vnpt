from app.schemas.chat import ChatMessage


def send_message(message: ChatMessage) -> dict:
    return {"status": "queued", "echo": message.content}