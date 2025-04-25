from flask import jsonify, request, g
import time
from functools import wraps
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.inspection import inspect
from pydantic import ValidationError
from flask import current_app
import jwt
import time
import threading
import math

SNOWFLAKE_CHAT = 1
SNOWFLAKE_MESSAGE = 2


def timestamp():
    return int(time.time())


def get_updatable_fields(model, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = set()
    return {c.key for c in inspect(model).mapper.column_attrs if c.key not in exclude_fields}


def handle_exceptions(f):
    from extensions import db

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as error:
            return jsonify({
                "error_code": "validate_error",
                "message": "Invalid request data",
                "data": error.errors(include_context=False, include_input=False, include_url=False)
            }), 400
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({"error_code": "db_error", "message": str(e.orig)}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error_code": "db_error", "message": str(e)}), 400
    return wrapper


def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
        else:
            return jsonify({"error_code": "require_login"}), 401

        try:
            data = jwt_decode(token)
            g._nth_decoded_jwt_payload = data
            return f(*args, **kwargs)
        except ValidationError as error:
            return jsonify({
                "error_code": "validate_error",
                "message": "Invalid request data",
                "data": error.errors(include_context=False, include_input=False, include_url=False)
            }), 400
        except Exception as e:
            return jsonify({"error_code": "error", "message": str(e)}), 400

    return wrapper



def jwt_encode(obj):
    return jwt.encode(obj, current_app.config['SECRET_KEY'], algorithm="HS256")


def jwt_decode(encoded):
    return jwt.decode(encoded, current_app.config['SECRET_KEY'], algorithms=["HS256"])


def get_user_from_jwt():
    dec = g.get('_nth_decoded_jwt_payload', None)
    if dec is None:
        raise RuntimeError(
            "Call require_login before using this func"
        )
    return dec


class SnowflakeGenerator:
    def __init__(self, type_code: int, node_id: int = 0, epoch: int = 1700000000000):
        self.epoch = epoch
        self.type_code = type_code & 0b11111
        self.node_id = node_id & 0b11111
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _timestamp(self):
        return int(time.time() * 1000) - self.epoch

    def _wait_next_millis(self, last_ts):
        ts = self._timestamp()
        while ts <= last_ts:
            ts = self._timestamp()
        return ts

    def generate_id(self):
        with self.lock:
            ts = self._timestamp()

            if ts == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0b111111111111  # 12 bit
                if self.sequence == 0:
                    ts = self._wait_next_millis(ts)
            else:
                self.sequence = 0

            self.last_timestamp = ts

            id_ = ((ts & ((1 << 42) - 1)) << 22) | \
                  (self.type_code << 17) | \
                  (self.node_id << 12) | \
                self.sequence

            return id_


def generate_chatid():
    chat = SnowflakeGenerator(type_code=SNOWFLAKE_CHAT)
    return chat.generate_id()


def generate_messageid():
    msg = SnowflakeGenerator(type_code=SNOWFLAKE_MESSAGE)
    return msg.generate_id()


def generate_snowflake(func_id):
    msg = SnowflakeGenerator(type_code=func_id)
    return msg.generate_id()


def parse_snowflake(snowflake_id: int, epoch: int = 1700000000000):
    timestamp = (snowflake_id >> 22) & ((1 << 42) - 1)
    type_code = (snowflake_id >> 17) & 0b11111
    node_id = (snowflake_id >> 12) & 0b11111
    sequence = snowflake_id & 0b111111111111

    actual_timestamp_ms = timestamp + epoch

    return {
        "timestamp": actual_timestamp_ms,
        "datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(actual_timestamp_ms / 1000)),
        "type_code": type_code,
        "node_id": node_id,
        "sequence": sequence
    }


def snowflake_to_timestamp(snowflake_id: int, ms=False, epoch: int = 1700000000000) -> int:
    timestamp = (snowflake_id >> 22) & ((1 << 42) - 1)

    actual_timestamp_ms = timestamp + epoch

    return actual_timestamp_ms if ms else math.floor(actual_timestamp_ms / 1000)
