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
    sleep_is_unhealthy = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def total_custom_minutes(self):
        start_min = self.sleep_start_time.hour * 60 + self.sleep_start_time.minute
        end_min = self.sleep_end_time.hour * 60 + self.sleep_end_time.minute
        if end_min <= start_min:
            end_min += 24 * 60
        return end_min - start_min

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sleep_start_time': self.sleep_start_time.strftime('%H:%M'),
            'sleep_end_time': self.sleep_end_time.strftime('%H:%M'),
            'timezone': self.timezone,
            'sleep_is_unhealthy': self.sleep_is_unhealthy,
            'total_custom_minutes': self.total_custom_minutes,
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


class UserProfile(db.Model):
    __tablename__ = 'user_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(64), default='')
    avatar_url = db.Column(db.String(256), default='')
    region = db.Column(db.String(64), default='')
    source_code = db.Column(db.String(64), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nickname': self.nickname or '',
            'avatar_url': self.avatar_url or '',
            'region': self.region or '',
            'source_code': self.source_code or '',
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


class UploadSession(db.Model):
    __tablename__ = 'upload_session'

    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default='active')
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def is_expired(self):
        return self.status != 'active' or datetime.utcnow() > self.expires_at


class UserOssFile(db.Model):
    __tablename__ = 'user_oss_files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    session_id = db.Column(db.String(36), nullable=False)
    friend_name = db.Column(db.String(64), nullable=False, default='')
    file_type = db.Column(db.String(16), nullable=False)
    bucket = db.Column(db.String(64), default='')
    object_key = db.Column(db.String(256), default='')
    content_text = db.Column(db.Text, default='')
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(64), default='')
    status = db.Column(db.String(16), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'friend_name': self.friend_name or '',
            'file_type': self.file_type,
            'bucket': self.bucket or '',
            'object_key': self.object_key or '',
            'content_text': self.content_text or '',
            'file_size': self.file_size or 0,
            'mime_type': self.mime_type or '',
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
