import json
from datetime import datetime

from .base import db


class AppConfig(db.Model):
    __tablename__ = 'sleep_app_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_type = db.Column(db.String(50), nullable=False, index=True)
    locale = db.Column(db.String(10), nullable=False, default='')
    data = db.Column(db.Text, nullable=False, default='{}')
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('config_type', 'locale', name='uk_type_locale'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'config_type': self.config_type,
            'locale': self.locale,
            'data': self.get_data(),
            'version': self.version,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def get_data(self):
        try:
            return json.loads(self.data) if isinstance(self.data, str) else self.data
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_data(self, data):
        self.data = json.dumps(data, ensure_ascii=False)
