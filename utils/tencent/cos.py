from qcloud_cos import CosConfig, CosServiceError
from qcloud_cos import CosS3Client
from django.conf import settings
from sts.sts import Sts


def create_bucket(bucket, region='ap-nanjing'):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)

    # 获取客户端对象
    client = CosS3Client(config)
    client.create_bucket(
        Bucket=bucket,
        ACL="public-read",  # 设置存储桶的 ACL，例如 'private'，'public-read'，'public-read-write'
    )
    # 设置bucket跨域配置
    cors_config = {
        'CORSRule': [
            {
                "AllowedOrigin": ["*"],
                "AllowedMethod": ["GET", "POST", "PUT", "DELETE", "HEAD"],
                'AllowedHeader': ['*'],
                'ExposeHeader': ['*'],
                'MaxAgeSeconds': 500
            }
        ]
    }
    client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_config
    )


def upload_file(bucket, body, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.upload_file_from_buffer(
        Bucket=bucket,
        Key=key,
        Body=body,
    )
    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)


def delete_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.delete_object(
        Bucket=bucket,
        Key=key,
    )


def check_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.head_object(
        Bucket=bucket,
        Key=key,
    )
    return response


def delete_file_list(bucket, region, key_list):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.delete_objects(
        Bucket=bucket,
        Delete=key_list,
    )


def credential(bucket, region):
    """获取临时凭证"""
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 1800,
        'secret_id': settings.TENCENT_COS_ID,
        # 固定密钥
        'secret_key': settings.TENCENT_COS_KEY,
        # 换成你的 bucket
        'bucket': bucket,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            # 'name/cos:PutObject',
            # 'name/cos:PostObject',
            # 分片上传
            # 'name/cos:InitiateMultipartUpload',
            # 'name/cos:ListMultipartUploads',
            # 'name/cos:ListParts',
            # 'name/cos:UploadPart',
            # 'name/cos:CompleteMultipartUpload',
            '*'
        ],

    }

    try:
        sts = Sts(config)
        response = sts.get_credential()
        return response
    except Exception as e:
        print(e)


def delete_bucket(bucket, region):
    """ 删除桶"""
    # 删除桶中所有文件
    # 删除桶中所有碎片
    # 删除桶
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)

    # 获取客户端对象
    client = CosS3Client(config)

    try:
        # 找到文件并删除
        while True:
            part_objects = client.list_objects(bucket)
            contents = part_objects.get('Contents')
            if not contents:
                break

            # 批量删除
            objects = {
                "Quiet": "true",
                "Object": [{"Key": item["Key"]} for item in contents]
            }
            client.delete_objects(bucket, objects)
            if part_objects["IsTruncated"] == "false":
                break
        # 碎片获取并删除
        while True:
            part_uploads = client.list_multipart_uploads(bucket)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
            if part_uploads["IsTruncated"] == "false":
                break
        client.delete_bucket(bucket)
    except CosServiceError as e:
        # 防止当存储桶不存在时删除桶报异常
        pass
