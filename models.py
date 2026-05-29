import json
from datetime import datetime, time

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SleepConfig(db.Model):
    __tablename__ = 'sleep_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    sleep_start_time = db.Column(db.Time, nullable=False)
    sleep_end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(64), nullable=False, default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sleep_start_time': self.sleep_start_time.strftime('%H:%M'),
            'sleep_end_time': self.sleep_end_time.strftime('%H:%M'),
            'timezone': self.timezone,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class UserStatus(db.Model):
    __tablename__ = 'user_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'reported_at': self.reported_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class Friendship(db.Model):
    __tablename__ = 'friendship'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_user_id = db.Column(db.String(64), nullable=False, index=True)
    to_user_id = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default='pending')
    apply_message = db.Column(db.String(256), default='')
    from_name = db.Column(db.String(64), default='')
    to_name = db.Column(db.String(64), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'status': self.status,
            'apply_message': self.apply_message,
            'from_name': self.from_name or '',
            'to_name': self.to_name or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class AppConfig(db.Model):
    __tablename__ = 'app_config'

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
