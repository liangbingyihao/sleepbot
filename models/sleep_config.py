from datetime import datetime

from .base import db


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


class SleepConfigHistory(db.Model):
    __tablename__ = 'sleep_config_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    sleep_start_time = db.Column(db.Time, nullable=False)
    sleep_end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(64), nullable=False, default='UTC')
    sleep_is_unhealthy = db.Column(db.Boolean, nullable=False, default=False)
    effective_from = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            'effective_from': self.effective_from.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
