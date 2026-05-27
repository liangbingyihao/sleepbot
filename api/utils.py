from functools import wraps

from flask import request, abort


def require_user_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            abort(401, '缺少 X-User-Id 请求头')
        return f(user_id, *args, **kwargs)
    return decorated
