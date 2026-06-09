import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'sleepbot')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}'
        f'@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
        f'?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', '')
    OSS_ENDPOINT_CN = os.getenv('OSS_ENDPOINT_CN', '')
    OSS_ENDPOINT_SG = os.getenv('OSS_ENDPOINT_SG', '')
    OSS_BUCKET_CN = os.getenv('OSS_BUCKET_CN', 'cn-bucket')
    OSS_BUCKET_SG = os.getenv('OSS_BUCKET_SG', 'sg-bucket')
    ASSET_SESSION_TTL = int(os.getenv('ASSET_SESSION_TTL', '86400'))

    UPLOAD_BASE_URL = os.getenv('UPLOAD_BASE_URL', 'http://localhost:5050')
