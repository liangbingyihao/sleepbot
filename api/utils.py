from functools import wraps

from flask import request, abort, g

# active 状态的确认窗口：其后 60 秒内若紧跟 awake，则视为一次真实解锁
ACTIVE_CONFIRM_SECONDS = 60

_LOCALE_ALIAS = {
    'zh': 'zh-CN', 'zh_cn': 'zh-CN', 'zh_hans': 'zh-CN', 'zh_hant': 'zh-CN', 'zho': 'zh-CN',
    'en': 'en', 'en_us': 'en',
}


def filter_confirmed_active(records):
    """丢弃未确认的 active 记录。

    records 必须已按 (reported_at, id) 升序排列。
    active 仅当其下一条记录为 awake、且间隔 <= ACTIVE_CONFIRM_SECONDS 时才保留。
    """
    result = []
    for i, r in enumerate(records):
        if r.status == 'active':
            nxt = records[i + 1] if i + 1 < len(records) else None
            if not nxt or nxt.status != 'awake':
                continue
            if (nxt.reported_at - r.reported_at).total_seconds() > ACTIVE_CONFIRM_SECONDS:
                continue
        result.append(r)
    return result


def _normalize_locale(locale):
    if not locale:
        return locale
    cleaned = locale.strip().lower().replace('-', '_')
    alias = _LOCALE_ALIAS.get(cleaned)
    return 'zh-CN' if alias == 'zh-CN' else 'en'


def require_user_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            abort(401, '缺少 X-User-Id 请求头')
        return f(user_id, *args, **kwargs)
    return decorated


def init_request_hooks(app):
    @app.before_request
    def normalize_language():
        locale = request.args.get('locale') or request.headers.get('X-Language', '')
        g.locale = _normalize_locale(locale)
