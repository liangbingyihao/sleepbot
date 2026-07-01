from datetime import datetime

from .base import db


class Users(db.Model):
    """外部用户表（只读），由其他服务维护"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(255), default='')
    avatar = db.Column(db.String(255), default='')
    membership_expired_at = db.Column(db.DateTime, nullable=True)
    lifetime_member = db.Column(db.Boolean, nullable=False, default=False)
    guest = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
