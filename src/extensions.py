from database.base import UnlockedAlchemy, BaseModel
from flask_bcrypt import Bcrypt
from faker import Faker
from flask_redis import FlaskRedis
from database.redis import CacheManager
db = UnlockedAlchemy(model_class=BaseModel)
bcrypt = Bcrypt()
faker = Faker()

redis_client = FlaskRedis()

cache = CacheManager()