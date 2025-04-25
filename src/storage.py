import oss2

from oss2.credentials import StaticCredentialsProvider
from config import Config
auth = oss2.ProviderAuthV2(StaticCredentialsProvider(access_key_id=Config.OSS_ACCESS_KEY_ID, access_key_secret=Config.OSS_ACCESS_KEY_SECRET))
bucket = oss2.Bucket(auth, Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)




