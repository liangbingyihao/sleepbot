import uuid
import logging
from datetime import datetime, timedelta, date

from flask import Blueprint, request, abort, current_app, send_from_directory, g
from werkzeug.utils import secure_filename

from models import db, UploadSession, UserOssFile, SystemMaterial, Users
from api.utils import require_user_id
from api.errors import ok
from api.assets_oss import get_bucket, presign_url, upload_to_oss, delete_from_oss
from api.report import (
    build_daily_report,
    build_weekly_report,
    build_monthly_report,
)

assets_bp = Blueprint('assets', __name__)
_logger = logging.getLogger(__name__)

_ALLOWED_MIME = {
    'image': {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/heic', 'image/heif'},
    'audio': {'audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/ogg', 'audio/x-m4a', 'audio/webm'},
}

MAX_FILE_SIZE = 5 * 1024 * 1024

_UPLOAD_MESSAGES = {
    'session_expired':   {'zh-CN': '上传链接已过期，请让好友重新生成', 'en': 'Upload link expired, please ask your friend to regenerate'},
    'missing_name':      {'zh-CN': '请输入你的昵称', 'en': 'Please enter your name'},
    'name_too_long':     {'zh-CN': '昵称过长', 'en': 'Name too long'},
    'invalid_type':      {'zh-CN': 'type 必须为 image、audio 或 text', 'en': 'type must be image, audio or text'},
    'library_full':      {'zh-CN': '该好友的素材库已满，无法继续上传', 'en': 'Friend library full, cannot upload more'},
    'empty_text':        {'zh-CN': '请输入文字内容', 'en': 'Please enter text content'},
    'text_too_long':     {'zh-CN': '文字内容过长', 'en': 'Text too long'},
    'missing_file':      {'zh-CN': '请选择文件', 'en': 'Please select a file'},
    'unsupported_format':{'zh-CN': '不支持的文件格式: {mime}', 'en': 'Unsupported file format: {mime}'},
    'file_too_large':    {'zh-CN': '文件大小不能超过 5MB', 'en': 'File size cannot exceed 5MB'},
    'oss_upload_failed':  {'zh-CN': '文件上传到云存储失败', 'en': 'File upload to cloud storage failed'},
}


def _msg(key, **kwargs):
    locale = getattr(g, 'locale', 'zh-CN')
    t = _UPLOAD_MESSAGES.get(key, {})
    s = t.get(locale, t.get('zh-CN', key))
    if kwargs:
        s = s.format(**kwargs)
    return s


def _display_width(s):
    w = 0
    for c in s:
        w += 2 if '\u4e00' <= c <= '\u9fff' else 1
    return w


def _check_length(text, key, max_width):
    if _display_width(text) > max_width:
        abort(400, _msg(key))


@assets_bp.route('/assets/session', methods=['POST'])
@require_user_id
def create_session(user_id):
    data = request.get_json(silent=True) or {}
    invite_code = (data.get('invite_code') or '').strip() or None

    session_id = str(uuid.uuid4())
    ttl = current_app.config['ASSET_SESSION_TTL']
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    base_url = current_app.config['UPLOAD_BASE_URL']

    UploadSession.query.filter(
        UploadSession.user_id == user_id,
        UploadSession.expires_at < datetime.utcnow(),
    ).delete()

    existing = UploadSession.query.filter_by(user_id=user_id) \
        .order_by(UploadSession.created_at.desc()).first()

    if existing and not existing.is_expired():
        existing.expires_at = expires_at
        if invite_code:
            existing.invite_code = invite_code
        session_id = existing.id
    elif existing:
        existing.id = session_id
        existing.expires_at = expires_at
        existing.invite_code = invite_code
    else:
        session = UploadSession(
            id=session_id,
            user_id=user_id,
            invite_code=invite_code,
            expires_at=expires_at,
        )
        db.session.add(session)
    db.session.commit()

    return ok({
        'session_id': session_id,
        'url': f'{base_url}/upload?session_id={session_id}',
        'invite_record': f'{base_url}/invite/record?session_id={session_id}',
        'invite_install': f'{base_url}/invite/install?session_id={session_id}',
        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@assets_bp.route('/assets/friend/session/<session_id>', methods=['GET'])
def session_info(session_id):
    _logger.info('session_info session_id=%s', session_id)
    session = UploadSession.query.get(session_id)
    if not session:
        abort(404, 'session 不存在')

    user = Users.query.filter_by(id=int(session.user_id)).first()
    creator_name = user.display_name if user and user.display_name else ''

    expired = session.is_expired()
    owner_id = session.user_id

    # 仅当显式传入合法 date/month 时才生成对应报告；否则维持旧输出
    date_str = request.args.get('date', '')
    day = None
    if date_str:
        try:
            day = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            _logger.warning('session_info invalid date=%s session_id=%s', date_str, session_id)

    month_str = request.args.get('month', '')
    year = month = None
    if month_str:
        try:
            parts = month_str.split('-')
            year, month = int(parts[0]), int(parts[1])
        except (ValueError, IndexError, TypeError):
            _logger.warning('session_info invalid month=%s session_id=%s', month_str, session_id)

    data = {
        'valid': not expired,
        'expired': expired,
        'expires_at': session.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
        'creator_name': creator_name,
        'invite_code': session.invite_code,
    }

    if day is not None:
        data['daily_report'] = None if expired else build_daily_report(owner_id, day)
        data['weekly_report'] = None if expired else build_weekly_report(owner_id, day)
    if year is not None and month is not None:
        data['monthly_report'] = None if expired else build_monthly_report(owner_id, year, month)

    return ok(data)


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
        abort(400, _msg('session_expired'))

    user_id = session.user_id

    friend_name = (request.form.get('friend_name') or '').strip()
    if not friend_name:
        _logger.warning('upload_file missing friend_name, session_id=%s', session_id)
        abort(400, _msg('missing_name'))
    _check_length(friend_name, 'name_too_long', 20)

    file_type = request.form.get('type')
    if file_type not in ('image', 'audio', 'text'):
        _logger.warning('upload_file invalid type=%s, session_id=%s', file_type, session_id)
        abort(400, _msg('invalid_type'))

    limit = current_app.config.get('MATERIAL_LIMIT', 30)
    count = UserOssFile.query.filter_by(user_id=user_id).filter(
        UserOssFile.source_system_material_id == 0
    ).count()
    if count >= limit:
        _logger.warning('upload_file material limit reached, user_id=%s, limit=%s', user_id, limit)
        abort(400, _msg('library_full'))

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
            abort(400, _msg('empty_text'))
        _check_length(text, 'text_too_long', 30)
        record.content_text = text
        record.mime_type = 'text/plain'
        _logger.info('upload_file text saved, session_id=%s', session_id)
    else:
        f = request.files.get('file')
        if not f or not f.filename:
            _logger.warning('upload_file no file, session_id=%s', session_id)
            abort(400, _msg('missing_file'))

        mime = f.content_type or 'application/octet-stream'
        allowed = _ALLOWED_MIME.get(file_type, set())
        _logger.info('upload_file file received, filename=%s, mime=%s, size=%s, session_id=%s',
                     f.filename, mime, request.content_length, session_id)

        if mime not in allowed:
            _logger.warning('upload_file unsupported mime=%s, session_id=%s', mime, session_id)
            abort(400, _msg('unsupported_format', mime=mime))

        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_SIZE:
            _logger.warning('upload_file file too large, size=%s, session_id=%s', size, session_id)
            abort(400, _msg('file_too_large'))

        ext = secure_filename(f.filename).rsplit('.', 1)[-1] if '.' in f.filename else ''
        object_key = f'{current_app.config["OSS_OBJECT_KEY_PREFIX"]}/{user_id}/{uuid.uuid4()}.{ext}'

        bucket = get_bucket('cn')

        _logger.info('upload_file oss start, bucket=%s, key=%s, session_id=%s',
                     bucket, object_key, session_id)
        try:
            upload_to_oss(bucket, object_key, f.read(), mime)
        except Exception as e:
            _logger.error('upload_file oss upload failed, bucket=%s, key=%s, error=%s',
                          bucket, object_key, str(e), exc_info=True)
            abort(500, _msg('oss_upload_failed'))

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
    locale = g.locale if hasattr(g, 'locale') and g.locale else 'zh-CN'

    sys_items = SystemMaterial.query.filter_by(locale=locale, is_active=True).order_by(SystemMaterial.sort_order.asc()).all()
    all_files = UserOssFile.query.filter_by(user_id=user_id).order_by(UserOssFile.created_at.desc()).all()

    if not all_files:
        all_sys = SystemMaterial.query.filter_by(is_active=True).all()
        for m in all_sys:
            if m.file_type not in ('text', 'audio'):
                continue
            db.session.add(UserOssFile(
                user_id=user_id,
                session_id='_system_',
                friend_name='',
                file_type=m.file_type,
                source_system_material_id=m.id,
                status='approved',
            ))
        db.session.commit()
        all_files = UserOssFile.query.filter_by(user_id=user_id).order_by(UserOssFile.created_at.desc()).all()

    adopted_map = {}
    materials = []

    for m in sys_items:
        ref = None
        for f in all_files:
            if f.source_system_material_id == m.id:
                ref = f
                break
        adopted_map[m.id] = ref
        item = m.to_dict()
        item['source'] = 'system'
        item['status'] = 'approved' if ref and ref.status == 'approved' else 'pending'
        item['_ts'] = (ref.updated_at if ref and ref.status == 'approved' else m.updated_at).timestamp()
        if m.file_type in ('image', 'audio') and m.object_key:
            item['presigned_url'] = presign_url(m.bucket, m.object_key)
        materials.append(item)

    limit = current_app.config.get('MATERIAL_LIMIT', 30)
    count = 0
    for f in all_files:
        if f.source_system_material_id:
            continue
        count += 1
        item = f.to_dict()
        item['source'] = 'friend'
        item['_ts'] = f.updated_at.timestamp()
        if f.file_type in ('image', 'audio') and f.object_key:
            item['presigned_url'] = presign_url(f.bucket, f.object_key)
        materials.append(item)

    materials.sort(key=lambda x: (x['status'] != 'approved', -x['_ts']))
    for item in materials:
        item.pop('_ts', None)
        item.pop('updated_at', None)

    full = count >= limit

    return ok({'materials': materials, 'full': full})


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
    if material.user_id != user_id or material.source_system_material_id:
        abort(403, '无权操作')

    if material.status == new_status:
        return ok(material.to_dict())
    valid = (
        (material.status == 'pending' and new_status in ('approved', 'rejected'))
        or (material.status == 'approved' and new_status == 'pending')
    )
    if not valid:
        abort(400, '不允许该状态变更')

    if new_status == 'rejected':
        if material.object_key:
            delete_from_oss(material.bucket, material.object_key)
        db.session.delete(material)
        db.session.commit()
        return ok(msg='已删除')

    if new_status == 'approved':
        old_approved = UserOssFile.query.filter_by(
            user_id=user_id,
            file_type=material.file_type,
            status='approved'
        ).all()
        for old in old_approved:
            old.status = 'pending'

    material.status = new_status
    db.session.commit()
    return ok(material.to_dict())


@assets_bp.route('/assets/materials/system/<int:sys_id>/adopt', methods=['POST'])
@require_user_id
def adopt_system_material(user_id, sys_id):
    """采用系统素材：建立引用记录并自动审批"""
    src = SystemMaterial.query.get(sys_id)
    if not src:
        abort(404, '系统素材不存在')

    # 同类型旧 approved → pending
    old_approved = UserOssFile.query.filter_by(
        user_id=user_id,
        file_type=src.file_type,
        status='approved'
    ).all()
    for old in old_approved:
        old.status = 'pending'

    m = UserOssFile.query.filter_by(
        user_id=user_id,
        source_system_material_id=sys_id,
    ).first()
    if m:
        m.status = 'approved'
    else:
        m = UserOssFile(
            user_id=user_id,
            session_id='_system_',
            friend_name='',
            file_type=src.file_type,
            source_system_material_id=sys_id,
            status='approved',
        )
        db.session.add(m)
    db.session.commit()
    return ok(m.to_dict())


@assets_bp.route('/assets/materials/system/<int:sys_id>/dismiss', methods=['DELETE'])
@require_user_id
def dismiss_system_material(user_id, sys_id):
    """取消采用：逻辑删除，status → pending"""
    m = UserOssFile.query.filter_by(
        user_id=user_id,
        session_id='_system_',
        source_system_material_id=sys_id,
    ).first()
    if not m:
        abort(404, '未采用该系统素材')

    m.status = 'pending'
    db.session.commit()
    return ok(msg='已取消采用')


# ====== 系统素材管理 ======


@assets_bp.route('/assets/system_materials', methods=['GET'])
@require_user_id
def get_system_materials(user_id):
    locale = g.locale if hasattr(g, 'locale') and g.locale else 'zh-CN'
    items = SystemMaterial.query.filter_by(locale=locale).order_by(SystemMaterial.sort_order.asc()).all()
    result = []
    for m in items:
        item = m.to_dict()
        if m.file_type in ('image', 'audio') and m.object_key:
            item['presigned_url'] = presign_url(m.bucket, m.object_key)
        result.append(item)
    return ok(result)


@assets_bp.route('/assets/system_materials', methods=['POST'])
@require_user_id
def add_system_material(user_id):
    """新增系统素材"""
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    file_type = data.get('file_type', 'image')
    locale = data.get('locale', 'zh-CN')

    m = SystemMaterial(
        file_type=file_type,
        content_text=data.get('content_text', ''),
        bucket=data.get('bucket', ''),
        object_key=data.get('object_key', ''),
        mime_type=data.get('mime_type', ''),
        locale=locale,
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True),
    )
    db.session.add(m)
    db.session.commit()
    return ok(m.to_dict())


@assets_bp.route('/assets/system_materials/<int:material_id>', methods=['PUT'])
@require_user_id
def update_system_material(user_id, material_id):
    """更新系统素材"""
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    m = SystemMaterial.query.get(material_id)
    if not m:
        abort(404, '系统素材不存在')

    for field in ('file_type', 'content_text', 'bucket', 'object_key',
                  'mime_type', 'locale', 'sort_order', 'is_active'):
        if field in data:
            setattr(m, field, data[field])

    db.session.commit()
    return ok(m.to_dict())


@assets_bp.route('/assets/system_materials/<int:material_id>', methods=['DELETE'])
@require_user_id
def delete_system_material(user_id, material_id):
    """删除系统素材"""
    m = SystemMaterial.query.get(material_id)
    if not m:
        abort(404, '系统素材不存在')

    if m.object_key:
        delete_from_oss(m.bucket, m.object_key)
    db.session.delete(m)
    db.session.commit()
    return ok(msg='删除成功')
