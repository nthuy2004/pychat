from database import Model
from sqlalchemy.orm import Mapped, mapped_column

from utils import snowflake_to_timestamp

CHAT_1V1 = 1
CHAT_GROUP = 2

class ChatRole:
    ROLE_NORMAL = 0
    ROLE_MOD = 1
    ROLE_OWNER = 2
    ROLE_PENDING = -1
    ROLE_MUTE = -2
    ROLE_BAN = -3

class ChatRelationship(Model):
    __tablename__ = "chat_relationship"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int]
    uid: Mapped[int]
    role: Mapped[str]
    time: Mapped[int]

    def can_delete_other_message(self):
        return self.role >= ChatRole.ROLE_MOD

class Chat(Model):
    __tablename__ = "chat"
    id : Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[int]
    owner: Mapped[int]
    name: Mapped[str] = mapped_column(default=None)
    avatar: Mapped[str] = mapped_column(default=None)
    rate_limit: Mapped[int] = mapped_column(default=0)
    pending_join: Mapped[bool] = mapped_column(default=False)

    def to_json(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "owner": self.owner,
            "name": self.name,
            "created_time": snowflake_to_timestamp(self.id),
            "avatar": self.avatar,
            "rate_limit": self.rate_limit,
            "pending_join": self.pending_join,
        }