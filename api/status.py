from datetime import datetime, timezone

from flask import Blueprint, request, abort

from models import db, UserStatus
from api.utils import require_user_id
from api.errors import ok

status_bp = Blueprint('status', __name__)

VALID_STATUSES = {'locked', 'active', 'idle', 'sleeping', 'awake'}


@status_bp.route('/status', methods=['POST'])
@require_user_id
def report_status(user_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    status = data.get('status')
    if not status:
        abort(400, 'status 为必填')

    if status not in VALID_STATUSES:
        abort(400, f'无效状态，可选值: {", ".join(sorted(VALID_STATUSES))}')

    record = UserStatus(user_id=user_id, status=status)

    reported_at = data.get('reported_at')
    if reported_at:
        try:
            dt = datetime.fromisoformat(reported_at)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            record.reported_at = dt
        except (ValueError, TypeError):
            abort(400, 'reported_at 格式错误，应为 ISO 时间')

    db.session.add(record)
    db.session.commit()

    return ok(record.to_dict())


@status_bp.route('/status/latest', methods=['GET'])
@require_user_id
def get_latest_status(user_id):
    record = UserStatus.query \
        .filter_by(user_id=user_id) \
        .order_by(UserStatus.reported_at.desc()) \
        .first()

    if not record:
        abort(404, '暂无状态记录')

    return ok(record.to_dict())


@status_bp.route('/status/history', methods=['GET'])
@require_user_id
def get_status_history(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    pagination = UserStatus.query \
        .filter_by(user_id=user_id) \
        .order_by(UserStatus.reported_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return ok({
        'items': [r.to_dict() for r in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    })
