from database import Model, Column
from extensions import db

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from extensions import bcrypt
from utils import jwt_encode

from database.redis import cache


from extensions import cache

class UserType:
    NORMAL = 0
    BOT = 1
class User(Model):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    display_name: Mapped[str]
    avatar: Mapped[str]
    bio: Mapped[str] = mapped_column(default=None)
    email: Mapped[str]
    phone: Mapped[str]
    color: Mapped[str]
    password: Mapped[str]
    created_at: Mapped[int]
    type: Mapped[int] = mapped_column(default=UserType.NORMAL)

    def create_jwt(self):
        return jwt_encode({"id": self.id, "username": self.username})
    
    def check_password(self, password: str):
        return bcrypt.check_password_hash(self.password, password)
    
    def get_display_name(self):
        return self.display_name if self.display_name else self.username

    def to_json(self):
        return {
            'id'         : str(self.id),
            'username'   : self.username,
            'display_name'  : self.display_name,
            'avatar'     : self.avatar,
            'bio'       : self.bio,
            'email'     : self.email,
            'phone'     : self.phone,
            'color'     : self.color,
            'created_at': self.created_at,
            'type': self.type
       }


def get_user_by_id(user_id: int):
    v = cache.get(f"user:{user_id}")
    if v is None:
        user = User.get(id=user_id)
        if user is not None:
            v = user.to_json()
            cache.set(f"user:{user_id}", v)
        else:
            return None
    return v