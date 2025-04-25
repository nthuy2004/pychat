import os

class DBConfig:
    db_type = os.getenv("DB_TYPE", "mysql")
    user = os.getenv("DB_USER", "root")
    passwd = os.getenv("DB_PASSWD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", 3306)
    db_name = os.getenv("DB_NAME", "pychat")
    db_uri = (
            f"mysql+pymysql://{user}:{passwd}@{host}:{port}/{db_name}?charset=utf8mb4"
        )
    redis_uri = "redis://localhost:6379"

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "catch_me_if_you_can")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "oh_my_god_hahahahahahhahh")
    JWT_TOKEN_LOCATION = os.getenv("JWT_TOKEN_LOCATION", ["headers"])
    JWT_HEADER_TYPE = os.getenv("JWT_HEADER_TYPE", "")

    USE_REDIS = True
    REDIS_URL = os.getenv("REDIS_URI", DBConfig.redis_uri)
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI", DBConfig.db_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_QUERY_TIMEOUT = 0.1
    SQLALCHEMY_RECORD_QUERIES = True

    OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
    OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME", "")

    CORS_HEADERS = "Content-Type"
