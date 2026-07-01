from datetime import datetime, time, timedelta

import pytz
from flask import Blueprint, request, abort

from models import db, Friendship, SleepConfig, Users, UserStatus
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

    target = Users.query.filter_by(public_id=to_user_id).first()
    if not target:
        abort(404, '用户不存在')

    from_name = (data.get('from_name') or '').strip()
    to_name = (data.get('to_name') or '').strip()

    existing = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.from_user_id == user_id, Friendship.to_user_id == target.id),
            db.and_(Friendship.from_user_id == target.id, Friendship.to_user_id == user_id),
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
        to_user_id=target.id,
        apply_message=apply_message,
        from_name=from_name,
        to_name=to_name,
        status="accepted"
    )
    db.session.add(friendship)
    db.session.commit()

    return ok(friendship.to_dict())


@supervision_bp.route('/friends/<int:friendship_id>', methods=['DELETE'])
@require_user_id
def delete_friendship(user_id, friendship_id):
    friendship = Friendship.query.get(friendship_id)
    if not friendship:
        abort(404, '好友关系不存在')

    if friendship.from_user_id != user_id and friendship.to_user_id != user_id:
        abort(403, '无权操作')

    if friendship.status == 'deleted':
        abort(400, '该好友关系已被删除')

    friendship.status = 'deleted'
    db.session.commit()
    return ok({'msg': '删除成功'})


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
    requests = Friendship.query.filter(
        Friendship.to_user_id == user_id,
        Friendship.status == 'pending',
    ).order_by(Friendship.created_at.desc()).all()

    return ok([r.to_dict() for r in requests])


@supervision_bp.route('/friends/requests/outgoing', methods=['GET'])
@require_user_id
def get_outgoing_requests(user_id):
    requests = Friendship.query.filter(
        Friendship.from_user_id == user_id,
        Friendship.status == 'pending',
    ).order_by(Friendship.created_at.desc()).all()

    return ok([r.to_dict() for r in requests])


@supervision_bp.route('/friends/<int:friendship_id>/name', methods=['PATCH'])
@require_user_id
def update_friend_name(user_id, friendship_id):
    friendship = Friendship.query.get(friendship_id)
    if not friendship:
        abort(404, '好友关系不存在')

    if friendship.status == 'deleted':
        abort(400, '该好友关系已被删除')

    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    name = data.get('name', '').strip()
    if not name:
        abort(400, 'name 为必填')

    if friendship.from_user_id == user_id:
        friendship.to_name = name
    elif friendship.to_user_id == user_id:
        friendship.from_name = name
    else:
        abort(403, '无权操作')

    db.session.commit()
    return ok(friendship.to_dict())


def _resolve_window(cfg):
    """根据当前时间和睡眠配置，计算 (in_window, local_date)

    in_window: 当前是否落在睡眠时段内
    local_date: 所在窗口的本地日期（在窗口内时取窗口日期；不在时取下个窗口日期）
    """
    if not cfg:
        return False, None

    tz = pytz.timezone(cfg.timezone)
    local_dt = tz.fromutc(datetime.utcnow())
    local_t = local_dt.time()
    start = cfg.sleep_start_time
    end = cfg.sleep_end_time

    if start < end:
        in_window = start <= local_t <= end
        local_date = local_dt.date()
        if not in_window and local_t >= end:
            local_date += timedelta(days=1)
    else:
        in_window = local_t >= start or local_t <= end
        local_date = local_dt.date()
        if in_window and local_t < start:
            local_date -= timedelta(days=1)
        elif not in_window and local_t > end:
            pass
    return in_window, local_date


def _next_window_utc(cfg):
    """返回最近一个睡眠窗口的 UTC 起止时间

    若当前落在窗口内 → 当前窗口；否则 → 即将到来的下个窗口
    返回 (start_str, end_str, is_active, start_dt, end_dt) 或 None
    """
    in_window, local_date = _resolve_window(cfg)
    if local_date is None:
        return None
    ws, we = _local_night_to_utc(cfg, local_date)
    return ws.strftime('%Y-%m-%d %H:%M:%S'), we.strftime('%Y-%m-%d %H:%M:%S'), in_window, ws, we


def _sleep_status(cfg, user_id):
    """计算当前 sleep_status

    返回: 'awake' | 'unlocked' | 'locked' | 'no_config'
    仅当落在睡眠时段内时，才查 DB：存在非 locked 记录才判 unlocked
    """
    in_window, local_date = _resolve_window(cfg)
    if local_date is None:
        return 'no_config'
    if not in_window:
        return 'awake'

    window_start, window_end = _local_night_to_utc(cfg, local_date)
    unlocked = UserStatus.query.filter(
        UserStatus.user_id == user_id,
        UserStatus.reported_at >= window_start,
        UserStatus.reported_at < window_end,
        UserStatus.status == 'active',
    ).first()
    return 'unlocked' if unlocked else 'locked'


def _local_night_to_utc(cfg, local_date):
    """将本地日期的睡眠窗口转为 UTC (start, end)"""
    tz = pytz.timezone(cfg.timezone)
    sh, sm = cfg.sleep_start_time.hour, cfg.sleep_start_time.minute
    eh, em = cfg.sleep_end_time.hour, cfg.sleep_end_time.minute

    local_start = datetime(local_date.year, local_date.month, local_date.day, sh, sm, 0)
    local_end = datetime(local_date.year, local_date.month, local_date.day, eh, em, 0)
    if local_end <= local_start:
        local_end += timedelta(days=1)

    start_utc = tz.localize(local_start).astimezone(pytz.utc).replace(tzinfo=None)
    end_utc = tz.localize(local_end).astimezone(pytz.utc).replace(tzinfo=None)
    return start_utc, end_utc


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
    poll_times = []
    now_utc = datetime.utcnow()
    fallback = now_utc + timedelta(seconds=60)

    for f in friendships:
        if f.from_user_id == user_id:
            friend_id = f.to_user_id
        else:
            friend_id = f.from_user_id

        sleep_config = SleepConfig.query.filter_by(user_id=friend_id).first()
        user = Users.query.filter_by(id=friend_id).first()
        window = _next_window_utc(sleep_config)

        result.append({
            'friendship_id': f.id,
            'user_id': friend_id,
            'friend_name': user.display_name if user else '',
            'friend_avatar': user.avatar if user else '',
            'apply_message': f.apply_message if f.from_user_id != user_id else '',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sleep_config': sleep_config.to_dict() if sleep_config else None,
            'sleep_status': _sleep_status(sleep_config, friend_id),
        })

        if window:
            _, _, active, ws_dt, we_dt = window
            if active:
                # 在窗口内：窗口结束时或 60 秒后，取较早者
                poll_times.append(min(we_dt, fallback))
            elif ws_dt > now_utc:
                # 不在窗口内：窗口开始时刷新
                poll_times.append(ws_dt)

    next_poll = min(poll_times) if poll_times else fallback
    next_poll_at = next_poll.strftime('%Y-%m-%d %H:%M:%S')

    result.sort(key=lambda f: (f['sleep_config'] is None, f['friendship_id']))

    return ok({'friends': result, 'next_poll_at': next_poll_at})
