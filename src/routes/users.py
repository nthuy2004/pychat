from flask import Flask, Blueprint

from controllers.users import profile, profile_patch, find_user

def reg_bp():
    bp = Blueprint("users_api", __name__, url_prefix="/users")

    bp.add_url_rule("/find", view_func=find_user, methods=["GET", "POST"])
    bp.add_url_rule("/<string:id>", view_func=profile, methods=["GET"])
    bp.add_url_rule("/<string:id>/profile", view_func=profile, methods=["GET"])
    bp.add_url_rule("/<string:id>/profile", view_func=profile_patch, methods=["PATCH"])

    return bp