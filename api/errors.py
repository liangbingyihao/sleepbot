from flask import jsonify
from werkzeug.exceptions import HTTPException

from models import db

OK = 'OK'
INVALID_PARAMETER = 'INVALID_PARAMETER'
AUTH_REQUIRED = 'AUTH_REQUIRED'
NOT_FOUND = 'NOT_FOUND'
INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
TOKEN_EXPIRED = 'TOKEN_EXPIRED'
MEMBERSHIP_REQUIRED = 'MEMBERSHIP_REQUIRED'
DUPLICATE_OPERATION = 'DUPLICATE_OPERATION'

_ERROR_MAP = {
    400: INVALID_PARAMETER,
    401: AUTH_REQUIRED,
    403: AUTH_REQUIRED,
    404: NOT_FOUND,
    405: INVALID_PARAMETER,
    500: INTERNAL_SERVER_ERROR,
}

_DEFAULT_MSG = {
    400: '请求参数错误',
    401: '需要用户认证',
    403: '无权访问',
    404: '资源未找到',
    405: '请求方法不允许',
    500: '服务器内部错误',
}

# werkzeug 内置的默认错误描述，用来识别 abort(code) 未传自定义消息的情况
_WERKZEUG_DEFAULTS = {
    400: "The browser (or proxy) sent a request that this server could not"
         " understand.",
    401: "The server could not verify that you are authorized to access"
         " the URL requested.  You either supplied the wrong credentials"
         " (e.g. a bad password), or your browser does not understand how"
         " to supply the credentials required.",
    403: "You don't have the permission to access the requested resource."
         " It is either read-protected or not readable by the server.",
    404: "The requested URL was not found on the server. If you entered the"
         " URL manually please check your spelling and try again.",
    405: "The method is not allowed for the requested URL.",
    500: "The server encountered an internal error and was unable to"
         " complete your request. Either the server is overloaded or there"
         " is an error in the application.",
}


def err(status_code, msg=None):
    code = _ERROR_MAP.get(status_code, INTERNAL_SERVER_ERROR)
    if msg is None or msg == _WERKZEUG_DEFAULTS.get(status_code):
        msg = _DEFAULT_MSG.get(status_code, '服务器内部错误')
    return jsonify({'code': code, 'msg': msg}), status_code


def ok(data=None, msg=None):
    body = {'code': OK}
    if data is not None:
        body['data'] = data
    if msg is not None:
        body['msg'] = msg
    return jsonify(body), 200


class AppError(Exception):
    def __init__(self, message, code=INVALID_PARAMETER, status_code=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({'code': e.code, 'msg': e.message}), e.status_code

    @app.errorhandler(400)
    def handle_400(e):
        return err(400, e.description)

    @app.errorhandler(404)
    def handle_404(e):
        return err(404, e.description)

    @app.errorhandler(405)
    def handle_405(e):
        return err(405, e.description)

    @app.errorhandler(500)
    def handle_500(e):
        db.session.rollback()
        return err(500)

    @app.errorhandler(Exception)
    def handle_unhandled(e):
        db.session.rollback()
        if isinstance(e, HTTPException):
            return err(e.code, e.description)
        return err(500)
