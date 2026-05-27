import pytz
from datetime import time

from flask import Blueprint, request, jsonify

from models import db, SleepConfig
from api.utils import require_user_id

sleep_config_bp = Blueprint('sleep_config', __name__)

_ALL_TZ = {tz for tz in pytz.all_timezones}


@sleep_config_bp.route('/config', methods=['GET'])
@require_user_id
def get_sleep_config(user_id):
    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if not config:
        return jsonify({'code': 'NOT_FOUND', 'msg': '睡眠配置未找到'}), 404
    return jsonify({'code': 'OK', 'data': config.to_dict()})


@sleep_config_bp.route('/config', methods=['POST'])
@require_user_id
def set_sleep_config(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': '请求体不能为空'}), 400

    sleep_start_str = data.get('sleep_start_time')
    sleep_end_str = data.get('sleep_end_time')
    if not sleep_start_str or not sleep_end_str:
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': 'sleep_start_time 和 sleep_end_time 为必填'}), 400

    try:
        start_h, start_m = map(int, sleep_start_str.split(':'))
        end_h, end_m = map(int, sleep_end_str.split(':'))
        sleep_start = time(start_h, start_m)
        sleep_end = time(end_h, end_m)
    except (ValueError, AttributeError):
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': '时间格式无效，请使用 HH:MM 格式'}), 400

    timezone = data.get('timezone', request.headers.get('X-Timezone', 'UTC'))
    if timezone not in _ALL_TZ:
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': f'无效时区，可用时区列表见 https://en.wikipedia.org/wiki/List_of_tz_database_time_zones'}), 400

    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if config:
        config.sleep_start_time = sleep_start
        config.sleep_end_time = sleep_end
        config.timezone = timezone
    else:
        config = SleepConfig(
            user_id=user_id,
            sleep_start_time=sleep_start,
            sleep_end_time=sleep_end,
            timezone=timezone,
        )
        db.session.add(config)

    db.session.commit()
    return jsonify({'code': 'OK', 'data': config.to_dict()})


@sleep_config_bp.route('/config', methods=['DELETE'])
@require_user_id
def delete_sleep_config(user_id):
    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if not config:
        return jsonify({'code': 'NOT_FOUND', 'msg': '睡眠配置未找到'}), 404

    db.session.delete(config)
    db.session.commit()
    return jsonify({'code': 'OK', 'msg': '删除成功'})
