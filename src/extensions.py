from database.base import UnlockedAlchemy, BaseModel
from flask_bcrypt import Bcrypt
from faker import Faker
from flask_redis import FlaskRedis
from database.redis import CacheManager
from openai import OpenAI
from google import genai

from config import Config

db = UnlockedAlchemy(model_class=BaseModel)
bcrypt = Bcrypt()
faker = Faker()

redis_client = FlaskRedis()

cache = CacheManager()

deepseek = OpenAI(api_key=Config.OPEN_AI_API, base_url="https://api.deepseek.com")

gemini = genai.Client(api_key=Config.GEMINI_API)