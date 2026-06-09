from functools import wraps

from flask import request, abort, g

_LOCALE_ALIAS = {
    'zh': 'zh-CN', 'zh_cn': 'zh-CN', 'zho': 'zh-CN',
    'zh_tw': 'zh-TW', 'cht': 'zh-TW',
    'en': 'en', 'en_us': 'en',
}


def _normalize_locale(locale):
    if not locale:
        return locale
    cleaned = locale.strip().lower().replace('-', '_')
    return _LOCALE_ALIAS.get(cleaned, locale)


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
