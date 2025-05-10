from utils import extract_user_ids

from models.message import Message, MessageType
from utils import generate_messageid
from models.user import get_user_by_id
from controllers.ws import broadcast_to_chat, broadcast_to_one

from flask import current_app

class BaseBot:
    def __init__(self, uid):
        self.uid = uid

    def is_valid_bot_request(self, message):
        if message['content'] is None:
            return False
        mentions = extract_user_ids(message['content'])
        return self.uid in mentions

    def on_message(self, chat_id, message, user):
        if message['uid'] == self.uid:
            return None

    def handle(self, chat_id, message, user):
        if not self.is_valid_bot_request(message):
            return
        print("handle bot...")
        self.chat_id = chat_id
        self.user = user
        self.message = message
        self.on_message(chat_id, message, user)

    def send_message(self, content, attachments=[], loading=False, reply_to_sender=True, save_to_db=True, only_send_to_sender=False, custom_message_id=None):
        id = generate_messageid() if custom_message_id is None else custom_message_id
        msg = Message(
            id=id,
            chat_id=self.chat_id,
            uid=self.uid,
            type=MessageType.NORMAL,
            content=content,
        )

        if reply_to_sender:
            msg.ref_chatid = self.chat_id,
            msg.ref_messageid = self.message["id"]

        if save_to_db:
            neww = msg.save(commit=True)
        else:
            neww = msg

        js = neww.to_json()
        js["attachments"] = attachments
        js["loading"] = loading

        if reply_to_sender:
            js["ref_message"] = self.message
        
        js['user'] = get_user_by_id(self.uid)

        if only_send_to_sender:
            broadcast_to_one(int(self.user["id"]), self.chat_id, "new_message", js)
        else:
            broadcast_to_chat(self.chat_id, "new_message", js)