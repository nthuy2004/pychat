from flask import Flask, make_response, request, Response
from config import Config

from flask_cors import CORS, cross_origin

from routes.api import reg_bp as api_bp

from flask_sock import Sock

from utils import jwt_decode
from controllers.ws import user_ws
import json

def create_app(config=Config):
    app = Flask(__name__)
    cors = CORS(app)
    app.config.from_object(config)
    reg_ext(app)
    reg_bp(app)
    return app


def reg_ext(app):
    from extensions import db, bcrypt, redis_client, cache
    db.init_app(app)
    bcrypt.init_app(app)
    redis_client.init_app(app)
    cache.init_app(redis_client)


def reg_bp(app):
    api_bp(app)







if __name__ == '__main__':
    app = create_app()
    sock = Sock(app)

    @sock.route("/ws")
    def websocket_route(ws):
        token = request.args.get("token")
        uid = 0

        try:
            uid = jwt_decode(token)["id"]
            if not uid:
                ws.send(json.dumps({"error_code": "ws_error", "message": "Invalid token"}))
                ws.close()
                return
        except Exception as e:
            ws.send(json.dumps({"error_code": "ws_error", "message": f"Invalid token {e}"}))
            ws.close()
            return
        
        print(f"[WS] User {uid} connected.")
        user_ws.setdefault(uid, []).append(ws)

        try:
            while True:
                msg = ws.receive()
                if msg is None:
                    break
                print(f"[WS] Received from {uid}: {msg}")
        except Exception as e:
            print(f"[WS] Error for user {uid}: {e}")
        finally:
            user_ws[uid].remove(ws)
            print(f"[WS] User {uid} disconnected.")

    @app.after_request
    def add_header(response):
        if request.method.lower() == 'options':
            return Response()
        return response
    app.run(debug=True)