from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='personel')
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                         nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    
    # İlişkiler
    person = db.relationship('Person', backref='user', lazy=True,
                           uselist=False)
    
    def set_password(self, password):
        """Şifreyi hashleyerek kaydet"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifreyi kontrol et"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Admin yetkisi kontrolü"""
        return self.role == 'admin'
    
    def is_manager(self):
        """Yönetici yetkisi kontrolü"""
        return self.role in ['admin', 'yonetici']
    
    def can_manage_users(self):
        """Kullanıcı yönetimi yetkisi"""
        return self.role in ['admin', 'yonetici']
    
    def can_manage_leaves(self):
        """İzin yönetimi yetkisi"""
        return self.role in ['admin', 'yonetici']
    
    def can_access_admin(self):
        """Admin paneli erişim yetkisi"""
        return self.role in ['admin', 'yonetici']


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_concurrent_leaves = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    members = db.relationship('Person', backref='team', lazy=True)


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'),
                       nullable=True)
    hire_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def annual_leave_entitlement(self):
        """Çalışma yılına göre yıllık izin hakkını hesapla"""
        years_of_service = (date.today() - self.hire_date).days // 365
        if years_of_service < 1:
            return 14
        elif years_of_service < 5:
            return 20
        else:
            return 26


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                         nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    person = db.relationship('Person', backref='leave_requests',
                           lazy=True)


class LeaveBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                         nullable=False)
    year = db.Column(db.Integer, nullable=False)
    entitlement = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Integer, default=0)
    pending = db.Column(db.Integer, default=0)
    carryover = db.Column(db.Integer, default=0)
    
    # İlişkiler
    person = db.relationship('Person', backref='leave_balances',
                           lazy=True)
    
    @property
    def remaining(self):
        """Kalan izin günü"""
        return self.entitlement + self.carryover - self.used - self.pending


class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    country = db.Column(db.String(10), default='TR')
    created_at = db.Column(db.DateTime, default=datetime.now)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                         nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    person = db.relationship('Person', backref='notifications',
                           lazy=True)


class BackupAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    leave_request_id = db.Column(db.Integer,
                                db.ForeignKey('leave_request.id'),
                                nullable=False)
    backup_person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                                nullable=False)
    responsibilities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    leave_request = db.relationship('LeaveRequest',
                                   backref='backup_assignments',
                                   lazy=True)
    backup_person = db.relationship('Person',
                                   backref='backup_assignments',
                                   lazy=True)


class LeavePolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'),
                       nullable=True)
    leave_type = db.Column(db.String(20), nullable=False)
    max_consecutive_days = db.Column(db.Integer)
    requires_approval = db.Column(db.Boolean, default=True)
    advance_notice_days = db.Column(db.Integer, default=7)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # İlişkiler
    team = db.relationship('Team', backref='leave_policies', lazy=True)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_blocking = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)