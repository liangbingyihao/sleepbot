from flask import Blueprint, request, abort

from models import db, UserProfile
from api.utils import require_user_id
from api.errors import ok

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile', methods=['GET'])
@require_user_id
def get_profile(user_id):
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        abort(404, '用户信息不存在')
    return ok(profile.to_dict())


@profile_bp.route('/profile', methods=['POST'])
@require_user_id
def init_profile(user_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    existing = UserProfile.query.filter_by(user_id=user_id).first()
    if existing:
        abort(400, '用户信息已存在')

    profile = UserProfile(
        user_id=user_id,
        nickname=(data.get('nickname') or '').strip(),
        avatar_url=(data.get('avatar_url') or '').strip(),
        region=(data.get('region') or '').strip(),
        source_code=(data.get('source_code') or '').strip(),
    )
    db.session.add(profile)
    db.session.commit()
    return ok(profile.to_dict())


@profile_bp.route('/profile/nickname', methods=['PATCH'])
@require_user_id
def update_nickname(user_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    nickname = (data.get('nickname') or '').strip()
    if not nickname:
        abort(400, 'nickname 为必填')

    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        abort(404, '用户信息不存在')

    profile.nickname = nickname
    db.session.commit()
    return ok(profile.to_dict())
