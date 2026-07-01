from datetime import datetime

from .base import db


class UploadSession(db.Model):
    __tablename__ = 'sleep_upload_session'

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
    __tablename__ = 'sleep_user_oss_files'

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
    source_system_material_id = db.Column(db.Integer, default=0)
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
            'source_system_material_id': self.source_system_material_id or 0,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class SystemMaterial(db.Model):
    __tablename__ = 'sleep_system_material'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_type = db.Column(db.String(16), nullable=False, default='image')
    content_text = db.Column(db.Text, default='')
    bucket = db.Column(db.String(64), default='')
    object_key = db.Column(db.String(256), default='')
    mime_type = db.Column(db.String(64), default='')
    locale = db.Column(db.String(10), nullable=False, default='zh-CN', index=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, presigned_url=''):
        return {
            'id': self.id,
            'file_type': self.file_type,
            'content_text': self.content_text or '',
            'bucket': self.bucket or '',
            'object_key': self.object_key or '',
            'mime_type': self.mime_type or '',
            'locale': self.locale,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'presigned_url': presigned_url or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
