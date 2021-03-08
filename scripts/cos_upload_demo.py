# -*- coding=utf-8
# appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
# 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

secret_id = 'AKID80cmhVQfqlPmTvm2sRm8EBxTyJOsteFc'  # 替换为用户的 secretId
secret_key = 'NXBZRB73oIVZgiFemleHEQnumNkX6Wue'  # 替换为用户的 secretKey
region = 'ap-nanjing'  # 替换为用户的 Region
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)

# 2. 获取客户端对象
client = CosS3Client(config)

# 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
response = client.upload_file(
    Bucket='bug-mgt-1259386016',
    LocalFilePath='init_user.py',  # 本地文件路径名
    Key='in_user.py',  # 上传到桶后的文件名
)
print(response['ETag'])
