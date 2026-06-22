import pytz
from datetime import time

from flask import Blueprint, request, abort

from models import db, SleepConfig
from api.utils import require_user_id
from api.errors import ok

sleep_config_bp = Blueprint('sleep_config', __name__)

_ALL_TZ = {tz for tz in pytz.all_timezones}


@sleep_config_bp.route('/config', methods=['GET'])
@require_user_id
def get_sleep_config(user_id):
    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if not config:
        abort(404, '睡眠配置未找到')
    return ok(config.to_dict())


@sleep_config_bp.route('/config', methods=['POST'])
@require_user_id
def set_sleep_config(user_id):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    sleep_start_str = data.get('sleep_start_time')
    sleep_end_str = data.get('sleep_end_time')
    if not sleep_start_str or not sleep_end_str:
        abort(400, 'sleep_start_time 和 sleep_end_time 为必填')

    try:
        start_h, start_m = map(int, sleep_start_str.split(':'))
        end_h, end_m = map(int, sleep_end_str.split(':'))
        sleep_start = time(start_h, start_m)
        sleep_end = time(end_h, end_m)
    except (ValueError, AttributeError):
        abort(400, '时间格式无效，请使用 HH:MM 格式')

    timezone = data.get('timezone', request.headers.get('X-Timezone', 'UTC'))
    if timezone not in _ALL_TZ:
        abort(400, f'无效时区，可用时区列表见 https://en.wikipedia.org/wiki/List_of_tz_database_time_zones')

    sleep_is_unhealthy = bool(data.get('sleep_is_unhealthy', False))

    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if config:
        config.sleep_start_time = sleep_start
        config.sleep_end_time = sleep_end
        config.timezone = timezone
        config.sleep_is_unhealthy = sleep_is_unhealthy
    else:
        config = SleepConfig(
            user_id=user_id,
            sleep_start_time=sleep_start,
            sleep_end_time=sleep_end,
            timezone=timezone,
            sleep_is_unhealthy=sleep_is_unhealthy,
        )
        db.session.add(config)

    db.session.commit()
    return ok(config.to_dict())


@sleep_config_bp.route('/config', methods=['DELETE'])
@require_user_id
def delete_sleep_config(user_id):
    config = SleepConfig.query.filter_by(user_id=user_id).first()
    if not config:
        abort(404, '睡眠配置未找到')

    db.session.delete(config)
    db.session.commit()
    return ok(msg='删除成功')
