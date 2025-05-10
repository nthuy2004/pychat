from flask import Flask, request
import json

from controllers.chat import get_chat_members

user_ws: dict[int, list] = {}



def broadcast_to_chat(chat_id, event, data):
    user_ids = get_chat_members(chat_id)
    for uid in user_ids:
        sockets = user_ws.get(uid.id, [])
        for ws in sockets:
            try:
                ws.send(json.dumps({
                    "event": event,
                    "chat_id": str(chat_id),
                    "data": data
                }))
            except Exception:
                continue

def broadcast_to_one(uid, chat_id, event, data):
    sockets = user_ws.get(uid, [])
    for ws in sockets:
        try:
            ws.send(json.dumps({
                "event": event,
                "chat_id": str(chat_id),
                "data": data
            }))
        except Exception:
            continue