from flask import jsonify
from werkzeug.exceptions import HTTPException

from models import db

_ERROR_MAP = {
    400: 'INVALID_PARAMETER',
    401: 'AUTH_REQUIRED',
    403: 'AUTH_REQUIRED',
    404: 'NOT_FOUND',
    405: 'INVALID_PARAMETER',
    500: 'INTERNAL_SERVER_ERROR',
}


class AppError(Exception):
    def __init__(self, message, code='INVALID_PARAMETER', status_code=400):
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
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': '请求参数错误'}), 400

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({'code': 'NOT_FOUND', 'msg': '资源未找到'}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({'code': 'INVALID_PARAMETER', 'msg': '请求方法不允许'}), 405

    @app.errorhandler(500)
    def handle_500(e):
        db.session.rollback()
        return jsonify({'code': 'INTERNAL_SERVER_ERROR', 'msg': '服务器内部错误'}), 500

    @app.errorhandler(Exception)
    def handle_unhandled(e):
        db.session.rollback()
        if isinstance(e, HTTPException):
            code = _ERROR_MAP.get(e.code, 'INTERNAL_SERVER_ERROR')
            return jsonify({'code': code, 'msg': e.description}), e.code
        return jsonify({'code': 'INTERNAL_SERVER_ERROR', 'msg': '服务器内部错误'}), 500
