import logging

from flask import current_app

_logger = logging.getLogger(__name__)


def get_bucket(region):
    if region and region.strip().lower() == 'cn':
        return current_app.config['OSS_BUCKET_CN']
    return current_app.config['OSS_BUCKET_SG']


def get_endpoint(bucket):
    cfg = current_app.config
    if bucket == cfg['OSS_BUCKET_SG']:
        return cfg['OSS_ENDPOINT_SG']
    return cfg['OSS_ENDPOINT_CN']


def get_oss_client(endpoint):
    from alibabacloud_oss_v2 import Config, Client
    from alibabacloud_oss_v2.credentials import StaticCredentialsProvider
    cfg = current_app.config

    region = endpoint.split('.')[0].replace('oss-', '', 1) if 'oss-' in endpoint else ''

    return Client(Config(
        region=region,
        endpoint=endpoint,
        credentials_provider=StaticCredentialsProvider(
            access_key_id=cfg['OSS_ACCESS_KEY_ID'],
            access_key_secret=cfg['OSS_ACCESS_KEY_SECRET'],
        ),
    ))


def presign_url(bucket, key):
    import alibabacloud_oss_v2 as oss
    client = get_oss_client(get_endpoint(bucket))
    result = client.presign(
        oss.GetObjectRequest(bucket=bucket, key=key),
    )
    return result.url


def upload_to_oss(bucket, key, file_data, mime_type):
    import alibabacloud_oss_v2 as oss
    endpoint = get_endpoint(bucket)
    _logger.debug('upload_to_oss bucket=%s key=%s endpoint=%s mime=%s data_len=%s',
                  bucket, key, endpoint, mime_type, len(file_data))
    client = get_oss_client(endpoint)
    client.put_object(
        oss.PutObjectRequest(
            bucket=bucket,
            key=key,
            body=file_data,
            content_type=mime_type,
        ),
    )
    _logger.debug('upload_to_oss done bucket=%s key=%s', bucket, key)


def delete_from_oss(bucket, key):
    import alibabacloud_oss_v2 as oss
    if not bucket or not key:
        _logger.debug('delete_from_oss skipped bucket=%s key=%s', bucket, key)
        return
    endpoint = get_endpoint(bucket)
    _logger.debug('delete_from_oss bucket=%s key=%s endpoint=%s', bucket, key, endpoint)
    client = get_oss_client(endpoint)
    client.delete_object(oss.DeleteObjectRequest(bucket=bucket, key=key))
    _logger.debug('delete_from_oss done bucket=%s key=%s', bucket, key)
