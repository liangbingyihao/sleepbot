import uuid
from datetime import datetime, timedelta

import json
from pathlib import Path

from flask import Blueprint, request, abort, current_app, send_from_directory
from werkzeug.utils import secure_filename

from models import db, UploadSession, UserOssFile
from api.utils import require_user_id
from api.errors import ok

assets_bp = Blueprint('assets', __name__)

_ALLOWED_MIME = {
    'image': {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
    'audio': {'audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/ogg', 'audio/x-m4a'},
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def _get_bucket(region):
    if region and 'sg' in region.lower():
        return current_app.config['OSS_BUCKET_SG']
    return current_app.config['OSS_BUCKET_CN']


def _get_endpoint(bucket):
    cfg = current_app.config
    if bucket == cfg['OSS_BUCKET_SG']:
        return cfg['OSS_ENDPOINT_SG']
    return cfg['OSS_ENDPOINT_CN']


def _get_oss_client(endpoint):
    import alibabacloud_oss_v2 as oss
    cfg = current_app.config
    return oss.Client(oss.LoadConfig(
        endpoint=endpoint,
        credentials=oss.CredentialsProvider(
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
    client = _get_oss_client(_get_endpoint(bucket))
    client.put_object(
        oss.PutObjectRequest(
            bucket=bucket,
            key=key,
            body=file_data,
            content_type=mime_type,
        ),
    )


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


@assets_bp.route('/assets/session/<session_id>', methods=['GET'])
def session_info(session_id):
    session = UploadSession.query.get(session_id)
    if not session:
        abort(404, 'session 不存在')
    return ok({
        'valid': not session.is_expired(),
        'expired': session.is_expired(),
        'expires_at': session.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@assets_bp.route('/assets/upload/<session_id>', methods=['GET'])
def upload_page(session_id):
    return send_from_directory(current_app.root_path, 'templates/upload.html')


@assets_bp.route('/assets/upload/<session_id>', methods=['POST'])
def upload_file(session_id):
    session = UploadSession.query.get(session_id)
    if not session or session.is_expired():
        abort(400, '上传链接已过期，请让好友重新生成')

    friend_name = (request.form.get('friend_name') or '').strip()
    if not friend_name:
        abort(400, '请输入你的昵称')

    file_type = request.form.get('type')
    if file_type not in ('image', 'audio', 'text'):
        abort(400, 'type 必须为 image、audio 或 text')

    record = UserOssFile(
        user_id=session.user_id,
        session_id=session_id,
        friend_name=friend_name,
        file_type=file_type,
        status='pending',
    )

    if file_type == 'text':
        text = (request.form.get('content') or '').strip()
        if not text:
            abort(400, '请输入文字内容')
        record.content_text = text
        record.mime_type = 'text/plain'
    else:
        f = request.files.get('file')
        if not f or not f.filename:
            abort(400, '请选择文件')

        mime = f.content_type or 'application/octet-stream'
        allowed = _ALLOWED_MIME.get(file_type, set())
        if mime not in allowed:
            abort(400, f'不支持的文件格式: {mime}')

        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_SIZE:
            abort(400, '文件大小不能超过 5MB')

        ext = secure_filename(f.filename).rsplit('.', 1)[-1] if '.' in f.filename else ''
        object_key = f'assets/{session.user_id}/{session_id}/{uuid.uuid4()}.{ext}'

        from models import UserProfile
        profile = UserProfile.query.filter_by(user_id=session.user_id).first()
        region = profile.region if profile else ''
        bucket = _get_bucket(region)

        _upload_to_oss(bucket, object_key, f.read(), mime)

        record.bucket = bucket
        record.object_key = object_key
        record.file_size = size
        record.mime_type = mime

    db.session.add(record)
    db.session.commit()
    return ok({'msg': '上传成功，感谢你的鼓励！'})


@assets_bp.route('/assets/materials', methods=['GET'])
@require_user_id
def get_materials(user_id):
    files = UserOssFile.query.filter_by(user_id=user_id).order_by(UserOssFile.created_at.desc()).all()

    result = []
    for f in files:
        item = f.to_dict()
        if f.file_type in ('image', 'audio') and f.object_key:
            item['presigned_url'] = _presign_url(f.bucket, f.object_key)
        result.append(item)

    return ok(result)


@assets_bp.route('/assets/materials/<int:material_id>/status', methods=['PATCH'])
@require_user_id
def review_material(user_id, material_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    new_status = data.get('status')
    if new_status not in ('approved', 'rejected'):
        abort(400, 'status 必须为 approved 或 rejected')

    material = UserOssFile.query.get(material_id)
    if not material:
        abort(404, '素材不存在')
    if material.user_id != user_id:
        abort(403, '无权操作')

    if material.status != 'pending':
        abort(400, '该素材已被审核')

    material.status = new_status
    db.session.commit()
    return ok(material.to_dict())
