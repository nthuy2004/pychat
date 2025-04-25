from typing import List, Optional
from database import Model
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class MessageType:
    NORMAL = 0
    POLL = 1
    SYSTEM = 2

class MessageAttachment(Model):
    __tablename__ = "message_attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int]
    content_type: Mapped[str]
    url: Mapped[str]

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
            "id": self.id,
            "chat_id": self.chat_id,
            "uid": self.uid,
            "type": self.type,
            "content": self.content,
            "edited_time": self.edited_time,
            "mention_everyone": self.mention_everyone,
            "ref_chatid": self.ref_chatid,
            "ref_messageid": self.ref_messageid,
            "pinned": self.pinned,
        }