from database import Model, Column
from extensions import db

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from extensions import bcrypt
from utils import jwt_encode
class User(Model):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    display_name: Mapped[str]
    avatar: Mapped[str]
    email: Mapped[str]
    phone: Mapped[str]
    color: Mapped[str]
    password: Mapped[str]
    created_at: Mapped[int]

    def create_jwt(self):
        return jwt_encode({"id": self.id, "username": self.username})
    
    def check_password(self, password: str):
        return bcrypt.check_password_hash(self.password, password)
    
    def get_display_name(self):
        return self.display_name if self.display_name else self.username

    def to_json(self):
        return {
            'id'         : self.id,
            'username'   : self.username,
            'display_name'  : self.display_name,
            'avatar'     : self.avatar,
            'email'     : self.email,
            'phone'     : self.phone,
            'color'     : self.color,
            'created_at': self.created_at,
       }
