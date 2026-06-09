from pathlib import Path

from flask import Flask, render_template

from config import Config
from models import db
from api.errors import register_error_handlers
from api.utils import init_request_hooks
from api.sleep_config import sleep_config_bp
from api.status import status_bp
from api.supervision import supervision_bp
from api.configs import configs_bp
from api.user_profile import profile_bp
from api.assets import assets_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_error_handlers(app)
    init_request_hooks(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(sleep_config_bp, url_prefix='/api/sleep')
    app.register_blueprint(status_bp, url_prefix='/api/sleep')
    app.register_blueprint(supervision_bp, url_prefix='/api/sleep')
    app.register_blueprint(configs_bp, url_prefix='/api/sleep')
    app.register_blueprint(profile_bp, url_prefix='/api/sleep')
    app.register_blueprint(assets_bp, url_prefix='/api/sleep')

    @app.route('/api/sleep/docs')
    def api_docs():
        md_path = Path(__file__).parent / 'docs' / 'api.md'
        import mistune
        html = mistune.html(md_path.read_text(encoding='utf-8'))
        return render_template('api_docs.html', content=html)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5050, debug=True)
