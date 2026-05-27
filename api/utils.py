from functools import wraps

from flask import request, jsonify


def require_user_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({'code': 'AUTH_REQUIRED', 'msg': '缺少 X-User-Id 请求头'}), 401
        return f(user_id, *args, **kwargs)
    return decorated
