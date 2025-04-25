from flask import Flask, Blueprint
from controllers.auth import login, register, logout

def reg_bp():
    bp = Blueprint("auth_api", __name__, url_prefix="/auth")
    
    bp.add_url_rule("/login", view_func=login, methods=["POST"])
    bp.add_url_rule("/register", view_func=register, methods=["POST"])
    bp.add_url_rule("/logout", view_func=logout, methods=["GET", "POST"])

    return bp