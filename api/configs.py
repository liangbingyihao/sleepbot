import random

from flask import Blueprint, abort, g, request

from models import db, AppConfig
from api.errors import ok

configs_bp = Blueprint('configs', __name__)


def _get_config(config_type, locale):
    cfg = AppConfig.query.filter_by(config_type=config_type, locale=locale).first()
    if not cfg:
        cfg = AppConfig.query.filter_by(config_type=config_type, locale='').first()
    return cfg


@configs_bp.route('/configs/<config_type>', methods=['GET'])
def get_config(config_type):
    cfg = _get_config(config_type, g.locale)
    if not cfg:
        abort(404, f'配置 {config_type} 不存在')
    return ok(cfg.to_dict())


@configs_bp.route('/configs/<config_type>', methods=['PUT'])
def update_config(config_type):
    data = request.get_json()
    if not data:
        abort(400, '请求体不能为空')

    cfg = AppConfig.query.filter_by(config_type=config_type, locale=g.locale).first()
    if cfg:
        cfg.set_data(data)
        cfg.version += 1
    else:
        cfg = AppConfig(config_type=config_type, locale=g.locale)
        cfg.set_data(data)
        db.session.add(cfg)

    db.session.commit()
    return ok(cfg.to_dict())


@configs_bp.route('/quiz/random', methods=['GET'])
def random_quiz():
    cfg = _get_config('quiz_questions', g.locale)
    if not cfg:
        abort(404, '题库不存在')

    questions = cfg.get_data().get('questions', [])
    if not questions:
        abort(404, '题库为空')

    question = random.choice(questions)
    return ok(question)
