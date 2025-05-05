from flask import request, jsonify
from pydantic import BaseModel, EmailStr, Field
from models.user import User
from utils import timestamp, handle_exceptions, require_login, get_user_from_jwt
from extensions import bcrypt, db, faker
from sqlalchemy import or_



def handle_login(user : User):
    return jsonify({"data": user.to_json(), "token": user.create_jwt()}), 200


class LoginRequest(BaseModel):
    username: str = Field(min_length=6)
    password: str = Field(min_length=6)

@handle_exceptions
def login():
    data = LoginRequest(**request.json).model_dump()

    user = User.query.filter_by(username=data["username"]).one_or_none()

    if user == None:
        return jsonify({"error_code": "wrong_credential", "data": "username", "message": "Tên người dùng không đúng"}), 401
    else:
        if not user.check_password(data["password"]):
            return jsonify({"error_code": "wrong_credential", "data": "password", "message": "Mật khẩu không đúng"}), 401
        return handle_login(user)

class RegisterRequest(BaseModel):
    username: str = Field(min_length=6)
    display_name: str = Field(default=None)
    avatar: str = Field(default=None)
    email: EmailStr
    phone: str = Field(default=None)
    password: str = Field(min_length=6)

@handle_exceptions
def register():
    data = RegisterRequest(**request.json).model_dump()

    enc_password = bcrypt.generate_password_hash(password=data['password']).decode("UTF-8")

    user = User(**data)
    user.password = enc_password
    user.created_at = timestamp()
    user.color = faker.hex_color()
    out = user.save()

    return handle_login(out)

@require_login
def logout():
    data = get_user_from_jwt()
    return jsonify(data), 200