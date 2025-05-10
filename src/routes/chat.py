from flask import Flask, Blueprint

from controllers.chat import get_list_bot, get_all_chat, get_one_chat_info, create_group, create_private, get_user_chat_state, delete_chat, leave_chat, get_all_messages, join_group, upload_attachments, delete_attachments
from controllers.message import send_message, edit_message, delete_message
def reg_bp():
    bp = Blueprint("chat_api", __name__, url_prefix="/chat")

    bp.add_url_rule("/", view_func=get_all_chat, methods=["GET"])
    bp.add_url_rule("/group", view_func=create_group, methods=["POST"])
    bp.add_url_rule("/private", view_func=create_private, methods=["POST"])
    bp.add_url_rule("/<int:chat_id>", view_func=get_one_chat_info, methods=["GET"])
    bp.add_url_rule("/<int:chat_id>/join", view_func=join_group, methods=["POST"])
    bp.add_url_rule("/<int:chat_id>/delete", view_func=delete_chat, methods=["POST"])
    bp.add_url_rule("/<int:chat_id>/leave", view_func=leave_chat, methods=["POST"])
    bp.add_url_rule("/<int:chat_id>/messages", view_func=get_all_messages, methods=["GET"])
    bp.add_url_rule("/<int:chat_id>/get_state", view_func=get_user_chat_state, methods=["GET"])
    bp.add_url_rule("/<int:chat_id>/messages", view_func=send_message, methods=["POST"])

    bp.add_url_rule("/<int:chat_id>/messages/<int:message_id>", view_func=edit_message, methods=["PATCH"])
    bp.add_url_rule("/<int:chat_id>/messages/<int:message_id>", view_func=delete_message, methods=["DELETE"])

    bp.add_url_rule("/<int:chat_id>/attachments", view_func=upload_attachments, methods=["POST"])
    bp.add_url_rule("/<int:chat_id>/attachments/<string:file_id>", view_func=delete_attachments, methods=["DELETE"])

    bp.add_url_rule("/list_bot", view_func=get_list_bot, methods=["GET"])

    return bp