from typing import List
from flask import request, jsonify
from models.chat import Chat, ChatRole, ChatRelationship
from models.message import Message, MessageAttachment, MessageType
from pydantic import BaseModel, HttpUrl
from models.user import User, get_user_by_id

from controllers.chat import get_message
from controllers.ws import broadcast_to_chat

from utils import handle_exceptions, generate_messageid, generate_attachmentid, require_login, get_user_from_jwt

from extensions import cache

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

        cache.delete(f"msg:{chat_id}:{message_id}")

        broadcast_to_chat(chat_id, "delete_message", str(message_id))

        return jsonify({"message": "OK"}), 200
    else:
        return jsonify({"error_code": "forbidden", "message": "Ai cho xoa ma xoa."}), 403

class AttachmentItem(BaseModel):
    mimetype: str
    original_filename: str
    upload_filename: str

class MessageRef(BaseModel):
    chat_id: str = ""
    message_id: str = ""

class SendMessageRequest(BaseModel):
    content: str
    attachments: List[AttachmentItem] = []
    message_ref: MessageRef = MessageRef()

@handle_exceptions
@require_login
def send_message(chat_id):
    uid = get_user_from_jwt()["id"]
    data = SendMessageRequest(**request.json).model_dump()

    if len(data['attachments']) == 0 and len(data["content"]) == 0:
        return jsonify({"error_code": "validate_error", "message": "?????????????"}), 400

    ref_chatid = data["message_ref"]["chat_id"]
    ref_mid = data["message_ref"]["message_id"]

    msg = Message(
        id=generate_messageid(),
        chat_id=chat_id,
        uid=uid,
        type=MessageType.NORMAL,
        content=data["content"],
    )

    if ref_chatid and ref_mid:
        msg.ref_chatid = ref_chatid
        msg.ref_messageid = ref_mid

    neww = msg.save()

    if neww is None:
        return jsonify({"error_code": "error", "message": "Can't send message"}), 500

    attachments = []

    for attachment in data['attachments']:
        a = MessageAttachment(
            id=generate_attachmentid(),
            message_id=neww.id,
            mimetype=attachment['mimetype'],
            original_filename=attachment['original_filename'],
            upload_filename=attachment['upload_filename']
        )

        asave = a.save()
        if asave:
            attachments.append(asave.to_json())


    js = neww.to_json()
    js["attachments"] = attachments

    if neww.ref_chatid and neww.ref_messageid:
        ref_msg = get_message(neww.ref_chatid, neww.ref_messageid)  # nêd optimize
        if ref_msg:                                                 # nêd optimize
            js["ref_message"] = ref_msg

    user = get_user_by_id(uid)
    if user:
        js["user"] = user

    broadcast_to_chat(chat_id, "new_message", js)

    return jsonify(js), 200