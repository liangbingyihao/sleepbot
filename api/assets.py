import uuid
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, abort, current_app, send_from_directory, g
from werkzeug.utils import secure_filename

from models import db, UploadSession, UserOssFile, SystemMaterial
from api.utils import require_user_id
from api.errors import ok
from api.assets_oss import get_bucket, presign_url, upload_to_oss, delete_from_oss

assets_bp = Blueprint('assets', __name__)
_logger = logging.getLogger(__name__)

_ALLOWED_MIME = {
    'image': {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/heic', 'image/heif'},
    'audio': {'audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/ogg', 'audio/x-m4a', 'audio/webm'},
}

MAX_FILE_SIZE = 5 * 1024 * 1024


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

    limit = current_app.config.get('MATERIAL_LIMIT', 30)
    count = UserOssFile.query.filter_by(user_id=user_id).filter(
        UserOssFile.source_system_material_id == 0
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
        bucket = get_bucket(region)

        _logger.info('upload_file oss start, bucket=%s, key=%s, session_id=%s',
                     bucket, object_key, session_id)
        try:
            upload_to_oss(bucket, object_key, f.read(), mime)
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
    locale = g.locale if hasattr(g, 'locale') and g.locale else 'zh-CN'

    sys_items = SystemMaterial.query.filter_by(locale=locale, is_active=True).order_by(SystemMaterial.sort_order.asc()).all()
    all_files = UserOssFile.query.filter_by(user_id=user_id).order_by(UserOssFile.created_at.desc()).all()

    if not all_files:
        for ft in ('text', 'audio'):
            default = next((m for m in sys_items if m.file_type == ft), None)
            if default:
                m = UserOssFile(
                    user_id=user_id,
                    session_id='_system_',
                    friend_name='',
                    file_type=default.file_type,
                    source_system_material_id=default.id,
                    status='approved',
                )
                db.session.add(m)
        db.session.commit()
        all_files = UserOssFile.query.filter_by(user_id=user_id).order_by(UserOssFile.created_at.desc()).all()

    adopted_map = {}
    materials = []

    # 系统素材（先展示）
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
        if m.file_type in ('image', 'audio') and m.object_key:
            item['presigned_url'] = presign_url(m.bucket, m.object_key)
        materials.append(item)

    # 好友素材（排后面），顺便计数
    limit = current_app.config.get('MATERIAL_LIMIT', 30)
    count = 0
    for f in all_files:
        if f.source_system_material_id:
            continue
        count += 1
        item = f.to_dict()
        item['source'] = 'friend'
        if f.file_type in ('image', 'audio') and f.object_key:
            item['presigned_url'] = presign_url(f.bucket, f.object_key)
        materials.append(item)

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
