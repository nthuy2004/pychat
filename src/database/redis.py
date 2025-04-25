from functools import wraps
import hashlib
from extensions import redis_client



def cache(expired=None):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            str = f"{f.__name__}:{args}:{kwargs}"
            key = hashlib.md5(str.encode()).hexdigest()

            r = redis_client.get()

