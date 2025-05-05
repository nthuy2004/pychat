from typing import List, Optional
from database import Model
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from utils import snowflake_to_timestamp
from storage import get_url

from extensions import cache
class MessageType:
    NORMAL = 0
    POLL = 1
    SYSTEM = 2

class MessageAttachment(Model):
    __tablename__ = "message_attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int]
    mimetype: Mapped[str]
    original_filename: Mapped[str]
    upload_filename: Mapped[str]
    def to_json(self):
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),       # conv to str bcz js browser can't handle bigint automatically
            "mimetype": self.mimetype,
            "original_filename": self.original_filename,
            "upload_filename": self.upload_filename,
            "upload_url": get_url(self.upload_filename),
        }

class Message(Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int]
    uid: Mapped[int]
    type: Mapped[int]
    content: Mapped[str]
    edited_time: Mapped[int] = mapped_column(default=0)
    mention_everyone: Mapped[bool] = mapped_column(default=False)
    ref_chatid: Mapped[int] = mapped_column(default=None)
    ref_messageid: Mapped[int] = mapped_column(default=None)
    pinned: Mapped[bool] = mapped_column(default=False)

    def to_json(self):
        return {
            "id": str(self.id),
            "chat_id": str(self.chat_id),       # conv to str bcz js browser can't handle bigint automatically
            "uid": str(self.uid),
            "type": self.type,
            "content": self.content,
            "edited_time": self.edited_time,
            "created_time": snowflake_to_timestamp(self.id),
            "mention_everyone": self.mention_everyone,
            "ref_chatid": str(self.ref_chatid) if self.ref_chatid else "",
            "ref_messageid": str(self.ref_messageid) if self.ref_messageid else "",
            "pinned": self.pinned,
        }


def get_message_by_id(chat_id: int, message_id: int):
    key = f"msg:{chat_id}:{message_id}"
    v = cache.get(key)
    if v is None:
        msg = Message.get(id=message_id, chat_id=chat_id)
        if msg is not None:
            v = msg.to_json()
            cache.set(key, v)
        else:
            return None
    return v

def get_attachment_by_msgid(message_id: int):
    #msg = MessageAttachment.get_all(message_id=message_id)

    cache_key = f"attach:{message_id}"
    v = cache.get(cache_key)
    if v is None:
        msg = MessageAttachment.get_all(message_id=message_id)
        if msg is not None:
            v = [m.to_json() for m in msg.all()]
            cache.set(cache_key, v)
        else:
            return []
    return v