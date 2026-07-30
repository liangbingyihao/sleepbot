from functools import wraps

from flask import request, abort, g

_LOCALE_ALIAS = {
    'zh': 'zh-CN', 'zh_cn': 'zh-CN', 'zh_hans': 'zh-CN', 'zh_hant': 'zh-CN', 'zho': 'zh-CN',
    'en': 'en', 'en_us': 'en',
}


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
