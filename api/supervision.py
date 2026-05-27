from flask import Blueprint, request, abort

from models import db, Friendship, SleepConfig, UserStatus
from api.utils import require_user_id
from api.errors import ok

supervision_bp = Blueprint('supervision', __name__)


@supervision_bp.route('/friends/requests', methods=['POST'])
@require_user_id
def send_friend_request(user_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    to_user_id = data.get('to_user_id')
    if not to_user_id:
        abort(400, 'to_user_id 为必填')

    if to_user_id == user_id:
        abort(400, '不能向自己发送好友申请')

    existing = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.from_user_id == user_id, Friendship.to_user_id == to_user_id),
            db.and_(Friendship.from_user_id == to_user_id, Friendship.to_user_id == user_id),
        ),
        Friendship.status.in_(['pending', 'accepted']),
    ).first()

    if existing:
        if existing.status == 'accepted':
            abort(400, '你们已经是好友了')
        abort(400, '已存在待处理的好友申请')

    apply_message = data.get('apply_message', '')

    friendship = Friendship(
        from_user_id=user_id,
        to_user_id=to_user_id,
        apply_message=apply_message,
    )
    db.session.add(friendship)
    db.session.commit()

    return ok(friendship.to_dict())


@supervision_bp.route('/friends/requests/<int:request_id>/respond', methods=['POST'])
@require_user_id
def respond_friend_request(user_id, request_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    action = data.get('action')
    if action not in ('accept', 'reject'):
        abort(400, 'action 必须为 accept 或 reject')

    friendship = Friendship.query.get(request_id)
    if not friendship:
        abort(404, '好友申请不存在')

    if friendship.to_user_id != user_id:
        abort(403, '无权操作该申请')

    if friendship.status != 'pending':
        abort(400, '该申请已被处理')

    friendship.status = 'accepted' if action == 'accept' else 'rejected'
    db.session.commit()

    return ok(friendship.to_dict())


@supervision_bp.route('/friends/requests/incoming', methods=['GET'])
@require_user_id
def get_incoming_requests(user_id):
    requests = Friendship.query.filter_by(
        to_user_id=user_id, status='pending'
    ).order_by(Friendship.created_at.desc()).all()

    return ok([r.to_dict() for r in requests])


@supervision_bp.route('/friends/requests/outgoing', methods=['GET'])
@require_user_id
def get_outgoing_requests(user_id):
    requests = Friendship.query.filter_by(
        from_user_id=user_id, status='pending'
    ).order_by(Friendship.created_at.desc()).all()

    return ok([r.to_dict() for r in requests])


@supervision_bp.route('/friends', methods=['GET'])
@require_user_id
def get_friends(user_id):
    friendships = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.from_user_id == user_id, Friendship.status == 'accepted'),
            db.and_(Friendship.to_user_id == user_id, Friendship.status == 'accepted'),
        ),
    ).all()

    result = []
    for f in friendships:
        friend_id = f.to_user_id if f.from_user_id == user_id else f.from_user_id

        sleep_config = SleepConfig.query.filter_by(user_id=friend_id).first()
        latest_status = UserStatus.query \
            .filter_by(user_id=friend_id) \
            .order_by(UserStatus.reported_at.desc()) \
            .first()

        result.append({
            'friendship_id': f.id,
            'user_id': friend_id,
            'apply_message': f.apply_message if f.from_user_id != user_id else '',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sleep_config': sleep_config.to_dict() if sleep_config else None,
            'latest_status': latest_status.to_dict() if latest_status else None,
        })

    return ok(result)
