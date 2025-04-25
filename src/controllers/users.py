from flask import jsonify, request
from utils import require_login, get_user_from_jwt, get_updatable_fields

from models.user import User

allow_update_fields = get_updatable_fields(User, exclude_fields={"id", "created_at", "password", "username"})

def get_uid(id : str):
    if id == "@me":
        return int(get_user_from_jwt()["id"])
    else:
        return int(id)

@require_login
def profile(id):
    uid = get_uid(id)

    user = User.get(id=uid)

    if user is None:
        return jsonify({"error_code": "user_not_found"}), 404
    else:
        return jsonify({"data": user.to_json()}), 200


@require_login
def profile_patch(id):
    uid = int(get_user_from_jwt()["id"])

    user = User.get(id=uid)

    data = request.get_json()

    if user is None:
        return jsonify({"error_code": "user_not_found"}), 404
    else:
        for field, value in data.items():
            if field in allow_update_fields:
                setattr(user, field, value)

        user.save()

        return jsonify({"data": user.to_json()}), 200