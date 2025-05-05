import oss2
import boto3
from botocore.config import Config as BOTOConfig

from oss2.credentials import StaticCredentialsProvider
from config import Config
auth = oss2.ProviderAuthV2(StaticCredentialsProvider(access_key_id=Config.OSS_ACCESS_KEY_ID, access_key_secret=Config.OSS_ACCESS_KEY_SECRET))

endp = "https://" + Config.OSS_ENDPOINT

print(endp)

bucket = oss2.Bucket(auth, "https://" + Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)

DIR_PREFIX = "video/fmimg"

def get_url(f):
    return f"https://{Config.OSS_BUCKET_NAME}.{Config.OSS_ENDPOINT}/{DIR_PREFIX}/{f}"

# s3_client = boto3.client(
#     's3',
#     config=BOTOConfig(s3={'addressing_style': 'virtual'}),
#     endpoint_url=Config.OSS_ENDPOINT,
#     region_name=Config.OSS_REGION,
#     aws_access_key_id=Config.OSS_ACCESS_KEY_ID,
#     aws_secret_access_key=Config.OSS_ACCESS_KEY_SECRET,
# )