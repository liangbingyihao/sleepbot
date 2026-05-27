from datetime import datetime

from flask import Blueprint, request, jsonify

from models import db, UserStatus
from api.utils import require_user_id

status_bp = Blueprint('status', __name__)

VALID_STATUSES = {'locked', 'active', 'idle', 'sleeping', 'awake'}


@status_bp.route('/status', methods=['POST'])
@require_user_id
def report_status(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': '请求体不能为空'}), 400

    status = data.get('status')
    if not status:
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': 'status 为必填'}), 400

    if status not in VALID_STATUSES:
        return jsonify({
            'code': 'INVALID_PARAMETER',
            'msg': f'无效状态，可选值: {", ".join(sorted(VALID_STATUSES))}'
        }), 400

    record = UserStatus(user_id=user_id, status=status)
    db.session.add(record)
    db.session.commit()

    return jsonify({'code': 'OK', 'data': record.to_dict()})


@status_bp.route('/status/latest', methods=['GET'])
@require_user_id
def get_latest_status(user_id):
    record = UserStatus.query \
        .filter_by(user_id=user_id) \
        .order_by(UserStatus.reported_at.desc()) \
        .first()

    if not record:
        return jsonify({'code': 'NOT_FOUND', 'msg': '暂无状态记录'}), 404

    return jsonify({'code': 'OK', 'data': record.to_dict()})


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

    return jsonify({
        'code': 'OK',
        'data': {
            'items': [r.to_dict() for r in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })
