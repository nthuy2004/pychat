from flask import Flask, Blueprint

from .users import reg_bp as users_bp
from .auth import reg_bp as auth_bp
from .chat import reg_bp as chat_bp

from flask import Blueprint

from models.user import get_user_by_id

def test():
    print(get_user_by_id(4))
    return "ok"

def reg_bp(app: Flask):
    bp = Blueprint("api_entry", __name__, url_prefix="/api")
    

    bp.add_url_rule("/test", view_func=test)

    bp.register_blueprint(users_bp())
    bp.register_blueprint(auth_bp())
    bp.register_blueprint(chat_bp())
    app.register_blueprint(bp)