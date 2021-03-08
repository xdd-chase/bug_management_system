"""
此配置文件用于自身开发各项配置，代码提供给测试时，剪切此配置文件，提交代码不要推此配置文件到git
"""
# 腾讯短信
TENCENT_SMS_APP_ID = 1400441044
TENCENT_SMS_APP_KEY = "b3c9800e1bc6ccb877bf583c2726c85d"

# 腾讯cos存储的id和key
TENCENT_COS_ID = 'AKID80cmhVQfqlPmTvm2sRm8EBxTyJOsteFc'  # 替换为用户的 secretId
TENCENT_COS_KEY = 'NXBZRB73oIVZgiFemleHEQnumNkX6Wue'  # 替换为用户的 secretKey

# 短信签名
TENCENT_SMS_SIGN = "点滴生活微记"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://10.32.66.161:6379",  # 安装redis的主机的 IP 和 端口
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 1000,
                "encoding": 'utf-8'
            },
            "PASSWORD": "foobared"  # redis密码
        }
    }
}
