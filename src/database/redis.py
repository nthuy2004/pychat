from functools import wraps
import hashlib
from sqlalchemy.ext.serializer import dumps, loads
from pickle import UnpicklingError

from .mock_obj import EmptyObject, empty

BUILTIN_TYPES = (int, bytes, str, float, bool)


def cache(expire=None, cache_key_format = None):
    from extensions import redis_client

    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            print(cache_key_format)
            str = f"{f.__name__}:{args}:{kwargs}"
            key = hashlib.md5(str.encode()).hexdigest()
            force = kwargs.pop("force", False)

            r = redis_client.get(key) if not force else None

            if r is None:
                r = f(*args, **kwargs)
                if r is not None:
                    if not isinstance(r, BUILTIN_TYPES):
                        r = dumps(r)
                    redis_client.set(key, r, expire)
                else:
                    r = dumps(empty)
                    redis_client.set(key, r, expire)
            try:
                r = loads(r)
            except (TypeError, UnpicklingError):
                pass
            if isinstance(r, EmptyObject):
                r = None
            if isinstance(r, bytes):
                r = r.decode()
            return r
        
        return wrapper
    return deco


class CacheManager():
    def __init__(self):
        pass

    def init_app(self, redis_client):
        self.redis_client = redis_client
        print("CacheManager initialized")

    def get(self, key, default=None):
        key = hashlib.md5(key.encode()).hexdigest()
        r = self.redis_client.get(key)
        if r is None:
            return default
        try:
            r = loads(r)
        except (TypeError, UnpicklingError):
            pass
        if isinstance(r, EmptyObject):
            r = default
        if isinstance(r, bytes):
            r = r.decode()
        return r

    def set(self, key, value):
        key = hashlib.md5(key.encode()).hexdigest()

        if value is not None:
            if not isinstance(value, BUILTIN_TYPES):
                value = dumps(value)
            self.redis_client.set(key, value)
        else:
            value = dumps(empty)
            self.redis_client.set(key, value)

    def delete(self, key):
        self.redis_client.delete(key)

    def exists(self, key):
        return self.redis_client.exists(key)