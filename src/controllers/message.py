from flask import request, jsonify
from models.chat import Chat, ChatRole, ChatRelationship
from models.message import Message, MessageAttachment, MessageType
from pydantic import BaseModel

from utils import handle_exceptions, generate_messageid, require_login, get_user_from_jwt

@require_login
def edit_message(chat_id, message_id):
    pass

@require_login
def delete_message(chat_id, message_id):
    uid = get_user_from_jwt()["id"]
    # owner, mod of chat_id and owner of message can delete it
    chat = Chat.get(id=chat_id)
    if chat is None:
        return jsonify({"error_code": "not_found", "message": "Chat ID not found."}), 404
    chat_rela = ChatRelationship.get(chat_id=chat_id, uid=uid)
    if chat_rela is None:
        return jsonify({"error_code": "not_found", "message": "User not join group."}), 404

    msg = Message.get(id=message_id, chat_id=chat_id)
    if msg is None:
        return jsonify({"error_code": "not_found", "message": "Message not found."}), 404

    is_owner = chat.owner == uid or chat_rela.can_delete_other_message()

    can_delete = msg.uid == uid or is_owner

    if can_delete:
        msg.delete()
        return jsonify({"message": "OK"}), 200
    else:
        return jsonify({"error_code": "forbidden", "message": "Ai cho xoa ma xoa."}), 403


class SendMessageRequest(BaseModel):
    content: str

@handle_exceptions
@require_login
def send_message(chat_id):
    uid = get_user_from_jwt()["id"]
    data = SendMessageRequest(**request.json).model_dump()

    msg = Message(
        id=generate_messageid(),
        chat_id=chat_id,
        uid=uid,
        type=MessageType.NORMAL,
        content=data["content"],
    )

    neww = msg.save()

    return jsonify(neww.to_json()), 200