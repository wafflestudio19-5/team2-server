from storages.backends.s3boto3 import S3Boto3Storage
# by default the storage class will always use AWS_S3_CUSTOM_DOMAIN in settings.py to generate url.

class S3MediaStorage(S3Boto3Storage):
    location = 'media'  # store files under directory media/


class S3StaticStorage(S3Boto3Storage):
    location = 'static'