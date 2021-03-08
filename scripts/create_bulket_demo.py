# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

secret_id = 'AKID80cmhVQfqlPmTvm2sRm8EBxTyJOsteFc'  # 替换为用户的 secretId
secret_key = 'NXBZRB73oIVZgiFemleHEQnumNkX6Wue'  # 替换为用户的 secretKey
region = 'ap-nanjing'  # 替换为用户的 Region
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)

# 2. 获取客户端对象
client = CosS3Client(config)
response = client.create_bucket(
    Bucket='test-1259386016',
    ACL="public-read",  # 设置存储桶的 ACL，例如 'private'，'public-read'，'public-read-write'
)
