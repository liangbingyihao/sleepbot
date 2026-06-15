import uuid
import logging
from datetime import datetime, timedelta

import json
from pathlib import Path

from flask import Blueprint, request, abort, current_app, send_from_directory
from werkzeug.utils import secure_filename

from models import db, UploadSession, UserOssFile
from api.utils import require_user_id
from api.errors import ok

assets_bp = Blueprint('assets', __name__)
_logger = logging.getLogger(__name__)

_ALLOWED_MIME = {
    'image': {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/heic', 'image/heif'},
    'audio': {'audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/ogg', 'audio/x-m4a', 'audio/webm'},
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def _get_bucket(region):
    if region and region.strip().lower() == 'cn':
        return current_app.config['OSS_BUCKET_CN']
    return current_app.config['OSS_BUCKET_SG']


def _get_endpoint(bucket):
    cfg = current_app.config
    if bucket == cfg['OSS_BUCKET_SG']:
        return cfg['OSS_ENDPOINT_SG']
    return cfg['OSS_ENDPOINT_CN']


def _get_oss_client(endpoint):
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


def _presign_url(bucket, key):
    import alibabacloud_oss_v2 as oss
    client = _get_oss_client(_get_endpoint(bucket))
    result = client.presign(
        oss.GetObjectRequest(bucket=bucket, key=key),
    )
    return result.url


def _upload_to_oss(bucket, key, file_data, mime_type):
    import alibabacloud_oss_v2 as oss
    endpoint = _get_endpoint(bucket)
    _logger.debug('_upload_to_oss bucket=%s key=%s endpoint=%s mime=%s data_len=%s',
                  bucket, key, endpoint, mime_type, len(file_data))
    client = _get_oss_client(endpoint)
    client.put_object(
        oss.PutObjectRequest(
            bucket=bucket,
            key=key,
            body=file_data,
            content_type=mime_type,
        ),
    )
    _logger.debug('_upload_to_oss done bucket=%s key=%s', bucket, key)


def _delete_from_oss(bucket, key):
    import alibabacloud_oss_v2 as oss
    if not bucket or not key:
        _logger.debug('_delete_from_oss skipped bucket=%s key=%s', bucket, key)
        return
    endpoint = _get_endpoint(bucket)
    _logger.debug('_delete_from_oss bucket=%s key=%s endpoint=%s', bucket, key, endpoint)
    client = _get_oss_client(endpoint)
    client.delete_object(oss.DeleteObjectRequest(bucket=bucket, key=key))
    _logger.debug('_delete_from_oss done bucket=%s key=%s', bucket, key)


@assets_bp.route('/assets/session', methods=['POST'])
@require_user_id
def create_session(user_id):
    session_id = str(uuid.uuid4())
    ttl = current_app.config['ASSET_SESSION_TTL']
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    base_url = current_app.config['UPLOAD_BASE_URL']

    session = UploadSession(
        id=session_id,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.session.add(session)
    db.session.commit()

    return ok({
        'session_id': session_id,
        'url': f'{base_url}/upload.html?session_id={session_id}',
        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@assets_bp.route('/assets/friend/session/<session_id>', methods=['GET'])
def session_info(session_id):
    _logger.info('session_info session_id=%s', session_id)
    session = UploadSession.query.get(session_id)
    if not session:
        abort(404, 'session 不存在')

    from models import UserProfile
    profile = UserProfile.query.filter_by(user_id=session.user_id).first()
    creator_name = profile.nickname if profile and profile.nickname else session.user_id

    return ok({
        'valid': not session.is_expired(),
        'expired': session.is_expired(),
        'expires_at': session.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
        'creator_name': creator_name,
    })


@assets_bp.route('/assets/friend/upload/<session_id>', methods=['GET'])
def upload_page(session_id):
    return send_from_directory(current_app.root_path, 'templates/upload.html')


@assets_bp.route('/assets/friend/upload/<session_id>', methods=['POST'])
def upload_file(session_id):
    _logger.info('upload_file called, session_id=%s, files=%s, form_keys=%s',
                 session_id, list(request.files.keys()), list(request.form.keys()))

    session = UploadSession.query.get(session_id)
    if not session or session.is_expired():
        _logger.warning('upload_file session expired or not found, session_id=%s', session_id)
        abort(400, '上传链接已过期，请让好友重新生成')

    user_id = session.user_id

    friend_name = (request.form.get('friend_name') or '').strip()
    if not friend_name:
        _logger.warning('upload_file missing friend_name, session_id=%s', session_id)
        abort(400, '请输入你的昵称')

    file_type = request.form.get('type')
    if file_type not in ('image', 'audio', 'text'):
        _logger.warning('upload_file invalid type=%s, session_id=%s', file_type, session_id)
        abort(400, 'type 必须为 image、audio 或 text')

    if file_type in ('image', 'audio'):
        limit = current_app.config.get('MATERIAL_LIMIT', 5)
        count = UserOssFile.query.filter_by(user_id=user_id).filter(
            UserOssFile.status != 'rejected',
            UserOssFile.file_type.in_(['image', 'audio']),
        ).count()
        if count >= limit:
            _logger.warning('upload_file material limit reached, user_id=%s, limit=%s', user_id, limit)
            abort(400, '该好友的素材库已满，无法继续上传')

    record = UserOssFile(
        user_id=user_id,
        session_id=session_id,
        friend_name=friend_name,
        file_type=file_type,
        status='pending',
    )

    if file_type == 'text':
        text = (request.form.get('content') or '').strip()
        if not text:
            _logger.warning('upload_file empty text, session_id=%s', session_id)
            abort(400, '请输入文字内容')
        record.content_text = text
        record.mime_type = 'text/plain'
        _logger.info('upload_file text saved, session_id=%s', session_id)
    else:
        f = request.files.get('file')
        if not f or not f.filename:
            _logger.warning('upload_file no file, session_id=%s', session_id)
            abort(400, '请选择文件')

        mime = f.content_type or 'application/octet-stream'
        allowed = _ALLOWED_MIME.get(file_type, set())
        _logger.info('upload_file file received, filename=%s, mime=%s, size=%s, session_id=%s',
                     f.filename, mime, request.content_length, session_id)

        if mime not in allowed:
            _logger.warning('upload_file unsupported mime=%s, session_id=%s', mime, session_id)
            abort(400, f'不支持的文件格式: {mime}')

        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_SIZE:
            _logger.warning('upload_file file too large, size=%s, session_id=%s', size, session_id)
            abort(400, '文件大小不能超过 5MB')

        ext = secure_filename(f.filename).rsplit('.', 1)[-1] if '.' in f.filename else ''
        object_key = f'assets/{user_id}/{uuid.uuid4()}.{ext}'

        from models import UserProfile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        region = profile.region if profile else 'cn'
        bucket = _get_bucket(region)

        _logger.info('upload_file oss start, bucket=%s, key=%s, session_id=%s',
                     bucket, object_key, session_id)
        try:
            _upload_to_oss(bucket, object_key, f.read(), mime)
        except Exception as e:
            _logger.error('upload_file oss upload failed, bucket=%s, key=%s, error=%s',
                          bucket, object_key, str(e), exc_info=True)
            abort(500, '文件上传到云存储失败')

        _logger.info('upload_file oss success, bucket=%s, key=%s, session_id=%s',
                     bucket, object_key, session_id)

        record.bucket = bucket
        record.object_key = object_key
        record.file_size = size
        record.mime_type = mime

    db.session.add(record)
    db.session.commit()
    _logger.info('upload_file done, record_id=%s, session_id=%s', record.id, session_id)
    return ok({'msg': '上传成功，感谢你的鼓励！'})


@assets_bp.route('/assets/materials', methods=['GET'])
@require_user_id
def get_materials(user_id):
    files = UserOssFile.query.filter_by(user_id=user_id).filter(UserOssFile.status != 'rejected').order_by(UserOssFile.created_at.desc()).all()

    result = []
    for f in files:
        item = f.to_dict()
        if f.file_type in ('image', 'audio') and f.object_key:
            item['presigned_url'] = _presign_url(f.bucket, f.object_key)
        result.append(item)

    limit = current_app.config.get('MATERIAL_LIMIT', 5)
    count = UserOssFile.query.filter_by(user_id=user_id).filter(
        UserOssFile.status != 'rejected',
        UserOssFile.file_type.in_(['image', 'audio']),
    ).count()
    full = count >= limit

    return ok({'materials': result, 'full': full})


@assets_bp.route('/assets/materials/<int:material_id>/status', methods=['PATCH'])
@require_user_id
def review_material(user_id, material_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    new_status = data.get('status')
    if new_status not in ('approved', 'rejected', 'pending'):
        abort(400, 'status 必须为 approved、rejected 或 pending')

    material = UserOssFile.query.get(material_id)
    if not material:
        abort(404, '素材不存在')
    if material.user_id != user_id:
        abort(403, '无权操作')

    valid = (
        (material.status == 'pending' and new_status in ('approved', 'rejected'))
        or (material.status == 'approved' and new_status == 'pending')
    )
    if not valid:
        abort(400, '不允许该状态变更')

    if new_status == 'rejected' and material.object_key:
        _delete_from_oss(material.bucket, material.object_key)

    material.status = new_status
    db.session.commit()
    return ok(material.to_dict())
