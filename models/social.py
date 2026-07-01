from datetime import datetime

from .base import db


class UserStatus(db.Model):
    __tablename__ = 'sleep_user_status'

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
    __tablename__ = 'sleep_friendship'

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
