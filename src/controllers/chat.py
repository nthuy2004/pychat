from flask import jsonify, request
from utils import require_login, get_user_from_jwt, generate_chatid, timestamp, handle_exceptions
from sqlalchemy import text, func

from models.chat import ChatRelationship, Chat
from models.user import User
from extensions import db, cache
from models.chat import CHAT_1V1, CHAT_GROUP, ChatRole

from pydantic import BaseModel, Field

from sqlalchemy.orm import aliased
from sqlalchemy import select, and_, desc

from models.message import Message, MessageType, get_message_by_id, get_attachment_by_msgid
from models.user import User, get_user_by_id

from utils import generate_messageid

def get_message(chat_id, message_id):
    m = get_message_by_id(chat_id, message_id)
    if m is None:
        return None

    u = get_user_by_id(m['uid'])

    if u:
        m["user"] = u

    m['attachments'] = get_attachment_by_msgid(message_id)

    return m

def get_or_create_private_chat_raw(user_a_id: int, user_b_id: int):
    with db.engine.begin() as conn:

        sql = text("""
            SELECT cr.chat_id
            FROM chat_relationship cr
            JOIN chat c ON c.id = cr.chat_id
            WHERE cr.uid IN (:a, :b)
            AND c.type = 1
            GROUP BY cr.chat_id
            HAVING COUNT(DISTINCT cr.uid) = 2
            LIMIT 1
        """)
        result = conn.execute(sql, {"a": user_a_id, "b": user_b_id}).fetchone()
        if result:
            return result[0]

        chid = generate_chatid()

        insert_chat = text("INSERT INTO chat (id, type, owner) VALUES (:id, 1, :owner)")
        conn.execute(insert_chat, {"id": chid, "owner": user_a_id})

        insert_relationship = text("""
            INSERT INTO chat_relationship (chat_id, uid, role, time)
            VALUES (:chat_id, :uid, :role, :time)
        """)

        conn.execute(insert_relationship, {"chat_id": chid, "uid": user_a_id, "role": ChatRole.ROLE_OWNER, "time": timestamp()})
        conn.execute(insert_relationship, {"chat_id": chid, "uid": user_b_id, "role": ChatRole.ROLE_NORMAL, "time": timestamp()})

        return chid


def get_1v1_recipient(chat_id):
    uid = get_user_from_jwt()["id"]

    recip = (
        db.session.query(User)
        .join(ChatRelationship, ChatRelationship.uid == User.id)
        .filter(ChatRelationship.chat_id == chat_id)
        .filter(ChatRelationship.uid != uid)
        .one_or_none()
    )

    return recip

class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1)
    avatar: str = Field(default=None)
    recipients: list = Field(default=[])

@handle_exceptions
@require_login
def create_group():
    uid = get_user_from_jwt()["id"]
    data = CreateGroupRequest(**request.json).model_dump()

    chat = Chat(
        id=generate_chatid(),
        type=CHAT_GROUP,
        owner=uid,
        name=data["name"],
        avatar=data["avatar"]
    )

    chat.save()

    ChatRelationship(chat_id=chat.id, uid=uid, role=ChatRole.ROLE_OWNER, time=timestamp()).save()

    recips = []

    for x in data["recipients"]:
        u = User.get(id=x)
        if u:
            ChatRelationship(chat_id=chat.id, uid=u.id, role=ChatRole.ROLE_NORMAL, time=timestamp()).save()
            recips.append(u.to_json())

    msg = Message(
        id=generate_messageid(),
        chat_id=chat.id,
        uid=uid,
        type=MessageType.SYSTEM,
        content="Đã tạo group", # ?
    )

    msg.save()

    return jsonify({
        "id": str(chat.id),
        "chat_id": str(chat.id),
        "name": chat.name,
        "owner": uid,
        "type": chat.type,
        "last_message": None,
        "last_message_id": str(msg.id),
        "last_chat_id": str(chat.id),
        "recipients": recips
    }), 200


class CreatePrivateRequest(BaseModel):
    recipient: str

@handle_exceptions
@require_login
def create_private():
    uid = get_user_from_jwt()["id"]
    data = CreatePrivateRequest(**request.json).model_dump()

    chat_id = get_or_create_private_chat_raw(uid, int(data["recipient"]))

    user = get_1v1_recipient(chat_id)

    return jsonify({
        "id": str(chat_id),
        "chat_id": str(chat_id),
        "name": user.get_display_name(),
        "owner": None,
        "type": CHAT_1V1,
        "last_message_id": None,
        "recipient": user.to_json()
    }), 200

@require_login
def get_all_chat():
    uid = get_user_from_jwt()["id"]

    with db.engine.begin() as conn:
        sql = text("""
            SELECT cr.chat_id, cr.role, c.type, c.owner, c.name, c.avatar, m.id as last_message_id, m.chat_id as last_chat_id
            FROM chat_relationship cr
            JOIN chat c ON c.id = cr.chat_id
            LEFT JOIN (
                SELECT chat_id, MAX(id) AS max_id
                FROM messages
                GROUP BY chat_id
            ) latest ON latest.chat_id = cr.chat_id
            LEFT JOIN messages m ON m.chat_id = latest.chat_id AND m.id = latest.max_id
            WHERE cr.uid = :id
        """)

        result = conn.execute(sql, {"id": uid}).all()

        results_as_dict = [u._asdict() for u in result]

        for x in results_as_dict:
            x["chat_id"] = str(x["chat_id"])    # cast to str bcz js browser can't handle bigint automatically
            if x["type"] == CHAT_1V1:
                recipient = get_1v1_recipient(x["chat_id"])
                x["recipient"] = recipient.to_json()
            if x["last_message_id"] and x["last_chat_id"]:
                x["last_message"] = get_message(x["last_chat_id"], x["last_message_id"])
                x["last_message_id"] = str(x["last_message_id"])
                x["last_chat_id"] = str(x["last_chat_id"])
            else:
                x["last_message"] = None

        return jsonify(results_as_dict), 200

    return ""


def delete_from_chatid(chat_id):
    with db.engine.begin() as conn:
        conn.execute(text("DELETE FROM `chat_relationship` WHERE `chat_id` = :chat_id"), {"chat_id": chat_id})
        conn.execute(text("DELETE FROM `chat` WHERE `id` = :chat_id"), {"chat_id": chat_id})

@require_login
def delete_chat(chat_id):
    uid = get_user_from_jwt()["id"]

    chat = Chat.get(id=chat_id)
    if chat is None:
        return jsonify({"error_code": "not_found", "data": "Chat ID not found!"}), 404

    can_delete = False

    ddd = ChatRelationship.get(chat_id=chat.id, uid=uid)

    if ddd is None:
        return jsonify({"error_code": "perm_denied", "message": "Join chưa mà xoá ?"}), 403
    else: can_delete = ddd.role == ChatRole.ROLE_OWNER

    if chat.type == CHAT_GROUP and chat.owner != uid and not can_delete:
        return jsonify({"error_code": "perm_denied", "message": "You can't delete this channel!"}), 403

    delete_from_chatid(chat_id)

    return jsonify({"message": "OK"}), 200

@require_login
def get_user_chat_state(chat_id):
    current_uid = get_user_from_jwt()["id"]
    chat = db.session.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    relationship = db.session.query(ChatRelationship).filter_by(
        chat_id=chat_id, uid=current_uid
    ).first()

    total_members = db.session.query(func.count()).select_from(ChatRelationship).filter_by(
        chat_id=chat_id
    ).scalar()

    c = chat.to_json()
    if chat.type == 1: #private
        r = get_1v1_recipient(chat_id)
        if r:
            c["recipient"] = r.to_json()

    return jsonify({
        "chat": c,
        "role": relationship.role if relationship else None,
        "total_members": total_members,
    })

@require_login
def join_group(chat_id):
    uid = get_user_from_jwt()["id"]

    chat = Chat.get(id=chat_id)

    if chat is None:
        return jsonify({"error_code": "not_found", "message": "Chat ID not found!"}), 404

    pending_join = chat.pending_join


    rela = ChatRelationship.get(chat_id=chat_id, uid=uid)

    if rela is None:
        # add
        if pending_join:
            ChatRelationship(chat_id=chat_id, uid=uid, role=ChatRole.ROLE_PENDING, time=timestamp()).save()
            return jsonify({"error_code": "pending_join", "message": "Waiting for admin to approve your join request."}), 403
        ChatRelationship(chat_id=chat_id, uid=uid, role=ChatRole.ROLE_NORMAL, time=timestamp()).save()
    else:
        if rela.role == ChatRole.ROLE_BAN:
            return jsonify({"error_code": "forbidden", "message": "You have been banned from this group!"}), 403
        if rela.role == ChatRole.ROLE_PENDING:
            return jsonify({"error_code": "pending_join", "message": "Waiting for admin to approve your join request."}), 403

    msg = Message(
        id=generate_messageid(),
        chat_id=chat.id,
        uid=uid,
        type=MessageType.SYSTEM,
        content=f"<@{uid}> đã tham gia nhóm"
    )

    msg.save()
    from controllers.ws import broadcast_to_chat
    broadcast_to_chat(chat_id, "new_message", get_message(msg.chat_id, msg.id))


    return jsonify({
        "id": chat.id,
        "name": chat.name,
        "owner": chat.owner,
        "type": chat.type,
        "avatar": chat.avatar,
        "last_message_id": None,
        "role": rela.role if rela else ChatRole.ROLE_NORMAL
    }), 200

@require_login
def leave_chat(chat_id):
    uid = get_user_from_jwt()["id"]

    chat = Chat.get(id=chat_id)
    if chat is None:
        return jsonify({"error_code": "not_found", "data": "Chat ID not found!"}), 404

    ddd = ChatRelationship.get(chat_id=chat.id, uid=uid)

    if ddd is None:
        return jsonify({"error_code": "perm_denied", "message": "Join chưa mà xoá ?"}), 403

    if chat.type == CHAT_GROUP and ddd.role == ChatRole.ROLE_BAN:
        return jsonify({"message": "OK"}), 200

    if chat.type == CHAT_1V1:
        delete_from_chatid(chat_id)
    else:
        """
        2 options:
        - 1: not admin, delete from chat_relationship only
        - 2: admin, move owner to someone
        """

        is_admin = chat.owner == uid or ddd.role == ChatRole.ROLE_OWNER

        if is_admin:
            # find nearest user to gain owner permission
            choose = (
                db.session.query(ChatRelationship)
                .filter(ChatRelationship.chat_id == id)
                .filter(ChatRelationship.uid != uid)
                .filter(ChatRelationship.role >= ChatRole.ROLE_NORMAL)
                .order_by(ChatRelationship.role.desc())
                .all()
            )
            
            if not choose:
                #k co ai thi xoa
                delete_from_chatid(id)
            else:
                # gain perm
                lalala = choose[0]
                lalala.update(True, role=ChatRole.ROLE_OWNER)
                ddd.delete()
                chat.update(True, owner=lalala.uid)
        else:
            ddd.delete()

    msg = Message(
        id=generate_messageid(),
        chat_id=chat.id,
        uid=uid,
        type=MessageType.SYSTEM,
        content=f"<@{uid}> đã rời nhóm"
    )

    msg.save()
    from controllers.ws import broadcast_to_chat
    broadcast_to_chat(chat_id, "new_message", get_message(msg.chat_id, msg.id))

    return jsonify({"message": "OK"}), 200



class GetAllMessagesRequest(BaseModel):
    limit: int = Field(default=50, min=1)
    before: int = Field(default=None)
    after: int = Field(default=None)


@handle_exceptions
@require_login
def get_all_messages(chat_id):
    uid = get_user_from_jwt()["id"]

    cond_data = GetAllMessagesRequest(**request.args).model_dump()

    check = ChatRelationship.get(chat_id=chat_id, uid=uid)

    # if check is None:
    #     return jsonify({"error_code": "perm_denied", "message": "Join chưa mà xem ?"}), 403
    
    if check and check.role == ChatRole.ROLE_BAN:
        return jsonify({"error_code": "perm_denied", "message": "Permission denied!"}), 403

    stmt = select(
        Message,
        User
    ).join(User, User.id == Message.uid).where(
        Message.chat_id == chat_id
    )

    if cond_data['before']:
        stmt = stmt.where(Message.id < cond_data['before'])
    if cond_data['after']:
        stmt = stmt.where(Message.id > cond_data['after'])

    stmt = stmt.order_by(desc(Message.id)).limit(cond_data['limit'])

    results = db.session.execute(stmt).all()

    messages = []
    for row in results:
        msg, user = row

        mdata = msg.to_json()

        v = cache.get(f"msg:{msg.chat_id}:{msg.id}")
        if v is None:
            cache.set(f"msg:{msg.chat_id}:{msg.id}", mdata)

        mdata["user"] = user.to_json()
        if msg.ref_chatid and msg.ref_messageid:
            ref_msg = get_message(msg.ref_chatid, msg.ref_messageid)
            if ref_msg:
                mdata["ref_message"] = ref_msg
        mdata["attachments"] = get_attachment_by_msgid(msg.id)
        messages.append(mdata)

    return jsonify(messages), 200


def upload_attachments(chat_id):
    from controllers.attachment import upload
    return upload()

def delete_attachments(chat_id, file_id):
    from controllers.attachment import remove
    return remove(file_id)

def get_chat_members(chat_id: int):
    members = (
        db.session.query(User)
        .join(ChatRelationship, User.id == ChatRelationship.uid)
        .filter(ChatRelationship.chat_id == chat_id,
                ChatRelationship.role > ChatRole.ROLE_PENDING
         )
        .all()
    )
    return members


@require_login
def get_one_chat_info(chat_id: int):
    uid = get_user_from_jwt()["id"]

    with db.engine.begin() as conn:
        sql = text("""
            SELECT cr.chat_id, cr.role, c.type, c.owner, c.name, c.avatar, m.id as last_message_id, m.chat_id as last_chat_id
            FROM chat_relationship cr
            JOIN chat c ON c.id = cr.chat_id
            LEFT JOIN (
                SELECT chat_id, MAX(id) AS max_id
                FROM messages
                GROUP BY chat_id
            ) latest ON latest.chat_id = cr.chat_id
            LEFT JOIN messages m ON m.chat_id = latest.chat_id AND m.id = latest.max_id
            WHERE cr.chat_id = :id AND c.id = :id AND cr.uid = :uid
        """)

        result = conn.execute(sql, {"id": chat_id, "uid": uid}).all()

        results_as_dict = [u._asdict() for u in result]

        if len(results_as_dict):
            x = results_as_dict[0]
            x["chat_id"] = str(x["chat_id"])    # cast to str bcz js browser can't handle bigint automatically
            if x["type"] == CHAT_1V1:
                recipient = get_1v1_recipient(x["chat_id"])
                x["recipient"] = recipient.to_json()
            if x["last_message_id"] and x["last_chat_id"]:
                x["last_message"] = get_message(x["last_chat_id"], x["last_message_id"])
                x["last_message_id"] = str(x["last_message_id"])
                x["last_chat_id"] = str(x["last_chat_id"])
            else:
                x["last_message"] = None

            return jsonify(x), 200

        return jsonify({"error_code": "not_found", "message": "Invalid request"}), 404

    return ""