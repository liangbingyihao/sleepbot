# 睡眠报告模块
# 提供日报/周报/月报三个接口，基于用户自定义睡眠时段 + 比例制三档判定
#
# 核心算法：
#   1. 锁屏时长：遍历睡眠窗口内的 UserStatus 时间线，locked 状态到下一事件的时间差累加
#   2. 解锁次数：locked → 非locked 的状态切换次数
#   3. 基线：最早3晚的平均玩手机时长（时段总时长 − 锁屏时长）
#   4. 挽回时长：基线玩手机 − 当晚玩手机，≥0 展示，<0 隐藏
#   5. 三档判定：success(>87.5%) / warning(≥62.5%) / danger(<62.5%)，基于时段总时长比例
from datetime import datetime, timedelta, date, time

import pytz

from flask import Blueprint, request, abort, g

from models import db, UserStatus, SleepConfig
from api.utils import require_user_id
from api.errors import ok

report_bp = Blueprint('report', __name__)

_BASELINE_MIN_NIGHTS = 3

_I18N = {
    'save_tip_negative': {
        'zh': '今晚解锁次数略有增加，明天继续稳住作息',
        'en': 'Unlock count was a bit higher tonight. Keep it up tomorrow!',
    },
    'save_tip_insufficient': {
        'zh': '积累3晚睡眠数据后，为你生成自律提升分析',
        'en': 'Accumulate 3 nights of sleep data to generate your self-discipline analysis',
    },
    'encourage_weekly': {
        'zh': '下周继续和搭档一起坚守作息，收获更好的睡眠吧',
        'en': 'Keep going with your partner next week and enjoy better sleep!',
    },
    'comment_unhealthy_base': {
        'zh': '整体睡眠时长不足，建议延长睡眠时段。',
        'en': 'Your overall sleep duration is insufficient. Consider extending your sleep window.',
    },
    'comment_great': {
        'zh': '本月自控力稳步提升，熬夜次数明显减少，继续保持',
        'en': 'Your self-control has steadily improved this month with noticeably fewer late nights. Keep it up!',
    },
    'comment_volatile': {
        'zh': '本月作息波动较大，下个月坚持早睡会越来越好的',
        'en': 'Your sleep schedule has been inconsistent this month. Stick with it and it will get better!',
    },
    'comment_normal': {
        'zh': '作息逐步改善中，继续和搭档一起加油吧',
        'en': 'Your sleep routine is gradually improving. Keep going with your partner!',
    },
    'fmt_hour': {
        'zh': '{h}小时',
        'en': '{h}h',
    },
    'fmt_hour_min': {
        'zh': '{h}小时{m}分',
        'en': '{h}h{m}m',
    },
    'fmt_min': {
        'zh': '{m}分钟',
        'en': '{m}m',
    },
    'fmt_zero': {
        'zh': '0分钟',
        'en': '0m',
    },
}


def _t(key, **kwargs):
    locale = g.locale if hasattr(g, 'locale') and g.locale else 'zh'
    lang = 'zh' if locale.startswith('zh') else 'en'
    entry = _I18N.get(key, {})
    text = entry.get(lang, key)
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace('{' + k + '}', str(v))
    return text


def _get_config(user_id):
    return SleepConfig.query.filter_by(user_id=user_id).first()


def _night_window(cfg, d):
    """返回用户睡眠窗口转为 UTC 的 (start_dt, end_dt)

    d 为用户本地日期。例如 Asia/Shanghai 用户设置 23:00–07:00：
    d=2026-06-22 → 23:00 CST ~ 07:00 CST = 15:00 UTC ~ 23:00 UTC
    """
    tz = pytz.timezone(cfg.timezone)
    sh, sm = cfg.sleep_start_time.hour, cfg.sleep_start_time.minute
    eh, em = cfg.sleep_end_time.hour, cfg.sleep_end_time.minute

    local_start = datetime(d.year, d.month, d.day, sh, sm, 0)
    local_end = datetime(d.year, d.month, d.day, eh, em, 0)
    if local_end <= local_start:
        local_end += timedelta(days=1)

    start_utc = tz.localize(local_start).astimezone(pytz.utc).replace(tzinfo=None)
    end_utc = tz.localize(local_end).astimezone(pytz.utc).replace(tzinfo=None)
    return start_utc, end_utc


def _get_statuses(user_id, start, end):
    return (
        UserStatus.query
        .filter_by(user_id=user_id)
        .filter(UserStatus.reported_at >= start, UserStatus.reported_at < end)
        .order_by(UserStatus.reported_at.asc())
        .all()
    )


def _calc_lock_seconds(user_id, start, end):
    """计算自定义时段内有效锁屏秒数"""
    records = _get_statuses(user_id, start, end)
    if not records:
        return 0

    total = 0
    for i in range(len(records)):
        cur = records[i]
        nxt = records[i + 1] if i + 1 < len(records) else None

        if cur.status == 'locked':
            until = nxt.reported_at if nxt else end
            total += (until - cur.reported_at).total_seconds()

    return int(total)


def _calc_unlock_count(user_id, start, end):
    """计算自定义时段内 locked → 非 locked 切换次数"""
    records = _get_statuses(user_id, start, end)
    count = 0
    for i in range(len(records) - 1):
        if records[i].status == 'locked' and records[i + 1].status != 'locked':
            count += 1
    return count


def _daily_status(lock_seconds, total_seconds):
    """比例制三档判定"""
    if total_seconds <= 0:
        return 'empty'
    if lock_seconds > total_seconds * 0.875:
        return 'success'
    elif lock_seconds >= total_seconds * 0.625:
        return 'warning'
    else:
        return 'danger'


def _fmt_duration(seconds):
    """秒数 → 多语言格式"""
    seconds = int(seconds)
    if seconds <= 0:
        return _t('fmt_zero')
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0 and minutes > 0:
        return _t('fmt_hour_min', h=hours, m=minutes)
    elif hours > 0:
        return _t('fmt_hour', h=hours)
    else:
        return _t('fmt_min', m=minutes)


def _fmt_minutes(seconds):
    return int(seconds // 60)


def _fmt_sleep_window(cfg):
    """格式化自定义时段为展示字符串，如 '22:30 – 06:30'"""
    s = cfg.sleep_start_time.strftime('%H:%M')
    e = cfg.sleep_end_time.strftime('%H:%M')
    return f'{s} – {e}'


def _calc_baseline(user_id, cfg):
    """计算个人基线：最早3晚平均玩手机时长（秒）

    从90天前的本地日期开始，依次检查每夜是否有数据，
    取最早3晚计算平均玩手机时长。
    返回 (baseline_play_seconds, total_nights)，总数<3时 baseline 为 None
    """
    tz = pytz.timezone(cfg.timezone)
    now_utc = datetime.utcnow()
    local_today = tz.fromutc(now_utc).date()
    first_day = local_today - timedelta(days=90)

    total_sec = cfg.total_custom_minutes * 60
    nights = []
    d = first_day
    while d <= local_today and len(nights) < _BASELINE_MIN_NIGHTS:
        start, end = _night_window(cfg, d)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            nights.append(lock_s)
        d += timedelta(days=1)

    if len(nights) < _BASELINE_MIN_NIGHTS:
        return None, len(nights)

    play_times = [total_sec - s for s in nights[:3]]
    return sum(play_times) // len(play_times), len(nights)


def _calc_saved_time(user_id, cfg, base_play, d):
    """计算单晚挽回时长

    base_play: 基线玩手机时长（秒）
    d: 计算日期
    返回 (saved_seconds, should_show)
    """
    start, end = _night_window(cfg, d)
    lock_s = _calc_lock_seconds(user_id, start, end)
    tonight_play = cfg.total_custom_minutes * 60 - lock_s
    saved = base_play - tonight_play
    if saved < 0:
        return 0, False
    return int(saved), True


def _success_streaks(day_list):
    """计算最大连续打卡天数"""
    current = 0
    max_streak = 0
    for d in day_list:
        if d['type'] == 'success':
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return current, max_streak


def _month_comment(avg_unlock, success_days, total_days, is_unhealthy):
    """生成月度自动评语"""
    if total_days < 5:
        return ''

    if is_unhealthy:
        base = _t('comment_unhealthy_base')
    else:
        base = ''

    if avg_unlock <= 1.0 and success_days >= total_days * 0.7:
        text = _t('comment_great')
    elif avg_unlock >= 3.0 or success_days < total_days * 0.4:
        text = _t('comment_volatile')
    else:
        text = _t('comment_normal')

    if is_unhealthy:
        return f'{text}。{base}'
    return text


def _build_day_list(cfg, user_id, days):
    """批量计算一组日期的锁屏数据和状态"""
    result = []
    for day in days:
        start, end = _night_window(cfg, day)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            result.append({
                'day': str(day.day),
                'type': _daily_status(lock_s, cfg.total_custom_minutes * 60),
            })
        else:
            result.append({
                'day': str(day.day),
                'type': 'empty',
            })
    return result


# ====== API 端点 ======
#
# 三个报告接口结构相似：
#   1. 解析日期参数
#   2. 读取用户 SleepConfig，获取自定义时段
#   3. 遍历日期范围内的每一天，计算锁屏秒数 → 解锁次数 → 三档判定
#   4. 计算基线 + 挽回时长（≥3晚有效记录才有）
#   5. 组装响应


@report_bp.route('/report/daily', methods=['GET'])
@require_user_id
def daily_report(user_id):
    """日报：单晚睡眠报告

    Query: ?date=YYYY-MM-DD
    """
    date_str = request.args.get('date', '')
    try:
        d = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        abort(400, 'date 格式错误，应为 YYYY-MM-DD')

    cfg = _get_config(user_id)
    if not cfg:
        abort(404, '未找到睡眠配置')

    start, end = _night_window(cfg, d)
    lock_s = _calc_lock_seconds(user_id, start, end)
    total_sec = cfg.total_custom_minutes * 60

    # 无数据 → 空态
    if lock_s <= 0:
        return ok({
            'type': 'day',
            'custom_sleep_time': _fmt_sleep_window(cfg),
            'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
            'lock_hour': '0分钟',
            'lock_seconds': 0,
            'unlock_count': 0,
            'day_type': 'empty',
            'show_save_time': False,
            'save_hour': '',
            'save_seconds': 0,
            'save_tip': '',
        })

    unlock = _calc_unlock_count(user_id, start, end)
    status = _daily_status(lock_s, total_sec)

    # 挽回时长：基线 ≥3晚 且 当日挽回 ≥0 才展示
    baseline, total_nights = _calc_baseline(user_id, cfg)
    show_save = False
    save_time = ''
    save_seconds = 0
    save_tip = ''

    if baseline is not None:
        saved, show_save = _calc_saved_time(user_id, cfg, baseline, d)
        if show_save:
            save_seconds = saved
            save_time = _fmt_duration(saved)

    if baseline is not None and not show_save:
        save_tip = _t('save_tip_negative')
    elif baseline is None and lock_s > 0:
        save_tip = _t('save_tip_insufficient')

    return ok({
        'type': 'day',
        'custom_sleep_time': _fmt_sleep_window(cfg),
        'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
        'lock_hour': _fmt_duration(lock_s),
        'lock_seconds': lock_s,
        'unlock_count': unlock,
        'day_type': status,
        'show_save_time': show_save,
        'save_hour': save_time,
        'save_seconds': save_seconds,
        'save_tip': save_tip,
    })


@report_bp.route('/report/weekly', methods=['GET'])
@require_user_id
def weekly_report(user_id):
    """周报：本周一~日汇总（含环比上周解锁变化率）

    Query: ?date=YYYY-MM-DD（取该日所在周的周一~周日）
    """
    date_str = request.args.get('date', '')
    try:
        d = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        abort(400, 'date 格式错误，应为 YYYY-MM-DD')

    cfg = _get_config(user_id)
    if not cfg:
        abort(404, '未找到睡眠配置')

    total_sec = cfg.total_custom_minutes * 60
    monday = d - timedelta(days=d.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    total_lock = 0
    total_unlock = 0
    success_count = 0
    days_with_data = 0
    day_list = []

    for day in days:
        start, end = _night_window(cfg, day)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            days_with_data += 1
            total_lock += lock_s
            total_unlock += _calc_unlock_count(user_id, start, end)
            day_type = _daily_status(lock_s, total_sec)
            if day_type == 'success':
                success_count += 1
        else:
            day_type = 'empty'
        day_list.append({'day': str(day.day), 'type': day_type})

    if days_with_data == 0:
        return ok({
            'type': 'week',
            'custom_sleep_time': _fmt_sleep_window(cfg),
            'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
            'total_lock_minute': 0,
            'total_lock_hour': '0小时',
            'success_day': 0,
            'avg_unlock': 0,
            'show_rate': False,
            'rate': 0,
            'total_save_hour': '',
            'encourage_text': _t('encourage_weekly'),
            'week_day_list': day_list,
        })

    avg_unlock = round(total_unlock / days_with_data, 1) if days_with_data > 0 else 0

    # 环比上周
    prev_monday = monday - timedelta(days=7)
    prev_days = [prev_monday + timedelta(days=i) for i in range(7)]
    prev_unlock = 0
    prev_with_data = 0
    for day in prev_days:
        start, end = _night_window(cfg, day)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            prev_unlock += _calc_unlock_count(user_id, start, end)
            prev_with_data += 1

    show_rate = prev_with_data >= 7
    rate = 0
    if show_rate and prev_unlock > 0:
        prev_avg = prev_unlock / prev_with_data
        if prev_avg > 0:
            rate = round((prev_avg - avg_unlock) / prev_avg * 100)

    # 挽回时长
    baseline, total_nights = _calc_baseline(user_id, cfg)
    total_save_hour = ''
    if baseline is not None:
        total_save = 0
        has_save = False
        for day in days:
            start, end = _night_window(cfg, day)
            if _calc_lock_seconds(user_id, start, end) > 0:
                saved, show = _calc_saved_time(user_id, cfg, baseline, day)
                if show and saved >= 0:
                    total_save += saved
                    has_save = True
        if has_save:
            total_save_hour = _fmt_duration(total_save)

    return ok({
        'type': 'week',
        'custom_sleep_time': _fmt_sleep_window(cfg),
        'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
        'total_lock_minute': _fmt_minutes(total_lock),
        'total_lock_hour': _fmt_duration(total_lock),
        'success_day': success_count,
        'avg_unlock': avg_unlock,
        'show_rate': show_rate,
        'rate': rate,
        'total_save_hour': total_save_hour,
        'encourage_text': _t('encourage_weekly'),
        'week_day_list': day_list,
    })


@report_bp.route('/report/monthly', methods=['GET'])
@require_user_id
def monthly_report(user_id):
    """月报：全月日历 + 解锁/打卡汇总（含环比上月、连续打卡、自动评语）

    Query: ?month=YYYY-MM
    """
    month_str = request.args.get('month', '')
    try:
        parts = month_str.split('-')
        year, month = int(parts[0]), int(parts[1])
    except (ValueError, IndexError, TypeError):
        abort(400, 'month 格式错误，应为 YYYY-MM')

    cfg = _get_config(user_id)
    if not cfg:
        abort(404, '未找到睡眠配置')

    total_sec = cfg.total_custom_minutes * 60

    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    total_days = last_day.day
    days = [first_day + timedelta(days=i) for i in range(total_days)]

    total_lock = 0
    total_unlock = 0
    success_count = 0
    days_with_data = 0
    day_list = []

    for day in days:
        start, end = _night_window(cfg, day)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            days_with_data += 1
            total_lock += lock_s
            total_unlock += _calc_unlock_count(user_id, start, end)
            day_type = _daily_status(lock_s, total_sec)
            if day_type == 'success':
                success_count += 1
        else:
            day_type = 'empty'
        day_list.append({'day': str(day.day), 'type': day_type})

    if days_with_data == 0:
        return ok({
            'type': 'month',
            'custom_sleep_time': _fmt_sleep_window(cfg),
            'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
            'month_total_hour': '0小时',
            'avg_day_hour': '0小时',
            'success_month_day': 0,
            'max_serial_day': 0,
            'show_save_time': False,
            'month_save_hour': '',
            'month_comment': '',
            'month_day_list': day_list,
        })

    avg_day_lock = total_lock // days_with_data if days_with_data > 0 else 0
    avg_unlock = round(total_unlock / days_with_data, 1) if days_with_data > 0 else 0
    _, max_streak = _success_streaks(day_list)

    # 环比上月
    prev_first, prev_last = _prev_month(year, month)
    prev_days = [prev_first + timedelta(days=i) for i in range((prev_last - prev_first).days + 1)]
    prev_unlock = 0
    prev_with_data = 0
    for day in prev_days:
        start, end = _night_window(cfg, day)
        lock_s = _calc_lock_seconds(user_id, start, end)
        if lock_s > 0:
            prev_unlock += _calc_unlock_count(user_id, start, end)
            prev_with_data += 1

    # 挽回时长
    baseline, total_nights = _calc_baseline(user_id, cfg)
    show_save = False
    month_save_hour = ''
    if baseline is not None:
        total_save = 0
        has_save = False
        for day in days:
            start, end = _night_window(cfg, day)
            if _calc_lock_seconds(user_id, start, end) > 0:
                saved, show = _calc_saved_time(user_id, cfg, baseline, day)
                if show and saved >= 0:
                    total_save += saved
                    has_save = True
        if has_save and total_save > 0:
            show_save = True
            month_save_hour = _fmt_duration(total_save)

    comment = _month_comment(avg_unlock, success_count, days_with_data, cfg.sleep_is_unhealthy)

    return ok({
        'type': 'month',
        'custom_sleep_time': _fmt_sleep_window(cfg),
        'sleep_is_unhealthy': cfg.sleep_is_unhealthy,
        'month_total_hour': _fmt_duration(total_lock),
        'avg_day_hour': _fmt_duration(avg_day_lock),
        'success_month_day': success_count,
        'max_serial_day': max_streak,
        'show_save_time': show_save,
        'month_save_hour': month_save_hour,
        'month_comment': comment,
        'month_day_list': day_list,
    })


def _prev_month(year, month):
    """返回上个月的第一天和最后一天"""
    if month == 1:
        return date(year - 1, 12, 1), date(year, 2, 1) - timedelta(days=1)
    if month == 12:
        return date(year, 11, 1), date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month - 1, 1), date(year, month + 1, 1) - timedelta(days=1)
