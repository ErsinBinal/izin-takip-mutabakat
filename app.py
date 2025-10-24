from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Person, Team, LeaveRequest, Holiday, LeaveBalance
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///izin_takip.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(hours=8)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Yetki kontrolü decorator'ı
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_access_admin():
            flash('Bu sayfaya erişim yetkiniz yok', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Login ve Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            login_user(user, remember=False)
            session.permanent = True
            user.last_login = datetime.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.can_access_admin():
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız', 'success')
    return redirect(url_for('login'))

# Ana sayfa
@app.route('/')
@login_required
def index():
    try:
        today = date.today()
        holidays = Holiday.query.filter(Holiday.date >= date(today.year, 1, 1)).order_by(Holiday.date).limit(30).all()
        upcoming = LeaveRequest.query.filter(LeaveRequest.start_date >= today, LeaveRequest.status == 'approved').order_by(LeaveRequest.start_date).limit(20).all()
        persons = Person.query.order_by(Person.name).all()
        return render_template('index.html', holidays=holidays, upcoming=upcoming, persons=persons)
    except Exception as e:
        return f"Template hatası: {str(e)}", 500


# Admin Panel (Kullanıcı yönetimi)

# Status sayfası - Bağlantı testi için
@app.route('/status')
def status():
    return render_template('status.html')

# Admin Panel (Kullanıcı yönetimi)
@app.route('/admin')
@login_required
@admin_required
def admin():
    with app.app_context():
        # Bekleyen izin taleplerini getir
        pending = LeaveRequest.query.filter_by(status='pending').all()
        
        # Yıllık izin özetini getir
        year = datetime.now().year
        summary = LeaveBalance.query.filter_by(year=year).join(Person).all()
        
        return render_template('admin.html',
                               pending=pending,
                               summary=summary,
                               year=year)

# İzin Talebi API'leri
@app.route('/api/leave/check', methods=['POST'])
@login_required
def check_leave():
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        person = Person.query.get_or_404(person_id)
        
        # Tarih aralığı kontrolü
        if start_date > end_date:
            return jsonify({'available': False, 'message': 'Başlangıç tarihi bitiş tarihinden sonra olamaz'})
        
        # Mevcut izinlerle çakışma kontrolü
        conflicts = LeaveRequest.query.filter(
            LeaveRequest.person_id == person_id,
            LeaveRequest.status.in_(['approved', 'pending']),
            db.or_(
                (LeaveRequest.start_date <= start_date) & (LeaveRequest.end_date >= start_date),
                (LeaveRequest.start_date <= end_date) & (LeaveRequest.end_date >= end_date),
                (LeaveRequest.start_date >= start_date) & (LeaveRequest.end_date <= end_date)
            )
        ).all()
        
        # Yıllık izin bakiyesi kontrolü
        requested_days = (end_date - start_date).days + 1
        year = start_date.year
        
        # Bu yıl kullanılan izin günlerini hesapla
        used_leaves = LeaveRequest.query.filter(
            LeaveRequest.person_id == person_id,
            LeaveRequest.status == 'approved',
            db.or_(
                (LeaveRequest.start_date <= start_date) & (LeaveRequest.end_date >= start_date),
                (LeaveRequest.start_date <= end_date) & (LeaveRequest.end_date >= end_date),
                (LeaveRequest.start_date >= start_date) & (LeaveRequest.end_date <= end_date)
            )
        ).all()
        
        used_days = sum([
            (min(lr.end_date, date(year, 12, 31)) - max(lr.start_date, date(year, 1, 1))).days + 1
            for lr in used_leaves
            if lr.start_date.year == year or lr.end_date.year == year
        ])
        
        # Yıllık izin limiti (varsayılan: 20 gün)
        annual_limit = 20
        remaining_days = annual_limit - used_days
        
        # Resmi tatiller
        holidays = Holiday.query.filter(
            Holiday.date >= start_date,
            Holiday.date <= end_date
        ).all()
        
        return jsonify({
            'available': len(conflicts) == 0 and remaining_days >= requested_days,
            'holidays': [{'date': h.date.strftime('%Y-%m-%d'), 'name': h.name} for h in holidays],
            'conflicts': [{'start': c.start_date.strftime('%Y-%m-%d'), 'end': c.end_date.strftime('%Y-%m-%d')} for c in conflicts],
            'used_days': used_days,
            'remaining_days': remaining_days,
            'message': 'İzin uygun' if len(conflicts) == 0 and remaining_days >= requested_days else 'İzin uygun değil'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leave/request', methods=['POST'])
@login_required
def request_leave():
    try:
        data = request.get_json()
        
        leave_request = LeaveRequest(
            person_id=data['person_id'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            reason=data.get('reason', ''),
            status='pending',
            created_at=datetime.now()
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({'message': 'İzin talebi başarıyla oluşturuldu'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/leave/approve/<int:request_id>', methods=['PUT'])
@login_required
@admin_required
def approve_leave(request_id):
    try:
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.username
        leave_request.approved_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'message': 'İzin talebi onaylandı'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/leave/reject/<int:request_id>', methods=['PUT'])
@login_required
@admin_required
def reject_leave(request_id):
    try:
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = 'rejected'
        leave_request.approved_by = current_user.username
        leave_request.approved_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'message': 'İzin talebi reddedildi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.can_manage_users():
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
    users = User.query.order_by(User.username).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
    } for user in users])

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if not current_user.can_manage_users():
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
    try:
        data = request.get_json()
        
        # Kullanıcı adı kontrolü
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
            
        # Email kontrolü
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Bu email adresi zaten kullanılıyor'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'Kullanıcı başarıyla oluşturuldu'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Kullanıcı adı kontrolü (kendisi hariç)
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
            
        # Email kontrolü (kendisi hariç)
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email and existing_email.id != user_id:
            return jsonify({'error': 'Bu email adresi zaten kullanılıyor'}), 400
        
        user.username = data['username']
        user.email = data['email']
        user.role = data['role']
        user.is_active = data.get('is_active', user.is_active)
        
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({'message': 'Kullanıcı başarıyla güncellendi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
        
    try:
        user = User.query.get_or_404(user_id)
        
        # Admin kullanıcısını silmeyi engelle
        if user.username == 'admin':
            return jsonify({'error': 'Admin kullanıcısı silinemez'}), 400
        
        # Kendini silmeyi engelle
        if user.id == current_user.id:
            return jsonify({'error': 'Kendi hesabınızı silemezsiniz'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Kullanıcı başarıyla silindi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Kullanıcı Yönetimi Web Routes
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()
    persons = Person.query.order_by(Person.name).all()
    # Kullanıcıları JSON'a serialize edilebilir hale getir
    users_json = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'person_id': u.person_id,
        'is_active': u.is_active,
        'last_login': u.last_login.strftime('%Y-%m-%d %H:%M:%S') if u.last_login else None
    } for u in users]
    return render_template('admin_users.html', users=users, users_json=users_json, persons=persons)

@app.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    try:
        # Form verilerini al
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        person_id = request.form.get('person_id')  # Opsiyonel
        
        # Kullanıcı adı kontrolü
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor', 'error')
            return redirect(url_for('admin_users'))
            
        # Email kontrolü
        if User.query.filter_by(email=email).first():
            flash('Bu email adresi zaten kullanılıyor', 'error')
            return redirect(url_for('admin_users'))
        
        user = User(
            username=username,
            email=email,
            role=role,
            person_id=int(person_id) if person_id else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kullanıcı başarıyla oluşturuldu', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        is_active = 'is_active' in request.form
        password = request.form.get('password')
        
        # Kullanıcı adı kontrolü (kendisi hariç)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Bu kullanıcı adı zaten kullanılıyor', 'error')
            return redirect(url_for('admin_users'))
            
        # Email kontrolü (kendisi hariç)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user_id:
            flash('Bu email adresi zaten kullanılıyor', 'error')
            return redirect(url_for('admin_users'))
        
        user.username = username
        user.email = email
        user.role = role
        user.is_active = is_active
        
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('Kullanıcı başarıyla güncellendi', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Admin kullanıcısını silmeyi engelle
        if user.username == 'admin':
            flash('Admin kullanıcısı silinemez', 'error')
            return redirect(url_for('admin_users'))
        
        # Kendini silmeyi engelle
        if user.id == current_user.id:
            flash('Kendi hesabınızı silemezsiniz', 'error')
            return redirect(url_for('admin_users'))
        
        db.session.delete(user)
        db.session.commit()
        flash('Kullanıcı başarıyla silindi', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

# İzin Bakiyesi Yönetimi
@app.route('/admin/leave-balances')
@login_required
@admin_required
def admin_leave_balances():
    year = request.args.get('year', datetime.now().year, type=int)
    balances = LeaveBalance.query.filter_by(year=year).join(Person).order_by(Person.name).all()
    return render_template('admin_leave_balances.html', balances=balances, year=year)

@app.route('/admin/leave-balances/update', methods=['POST'])
@login_required
@admin_required
def admin_update_leave_balance():
    try:
        person_id = request.form['person_id']
        year = int(request.form['year'])
        annual_leave = int(request.form['annual_leave'])
        used_leave = int(request.form['used_leave'])
        
        balance = LeaveBalance.query.filter_by(person_id=person_id, year=year).first()
        if not balance:
            balance = LeaveBalance(person_id=person_id, year=year)
            db.session.add(balance)
        
        balance.annual_leave = annual_leave
        balance.used_leave = used_leave
        
        db.session.commit()
        flash('İzin bakiyesi güncellendi', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('admin_leave_balances'))

# API Endpoints
@app.route('/api/holidays', methods=['GET'])
@login_required
def get_holidays():
    holidays = Holiday.query.order_by(Holiday.date).all()
    return jsonify([{
        'id': h.id,
        'date': h.date.strftime('%Y-%m-%d'),
        'name': h.name
    } for h in holidays])

@app.route('/api/persons', methods=['GET'])
@login_required
def get_persons():
    persons = Person.query.order_by(Person.name).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'email': p.email,
        'team_id': p.team_id,
        'team_name': p.team.name if p.team else None
    } for p in persons])

@app.route('/api/teams', methods=['GET'])
@login_required
def get_teams():
    teams = Team.query.order_by(Team.name).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'manager': t.manager
    } for t in teams])

@app.route('/api/leave-requests', methods=['GET'])
@login_required
def get_leave_requests():
    requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'person_name': r.person.name,
        'start_date': r.start_date.strftime('%Y-%m-%d'),
        'end_date': r.end_date.strftime('%Y-%m-%d'),
        'reason': r.reason,
        'status': r.status,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for r in requests])

@app.route('/api/admin/person/list', methods=['GET'])
@login_required
def admin_person_list():
    if not current_user.can_access_admin():
        return jsonify({'error': 'Yetkiniz yok'}), 403
        
    persons = Person.query.order_by(Person.name).all()
    
    return jsonify([{
        'id': person.id,
        'name': person.name,
        'email': person.email,
        'team_name': person.team.name if person.team else 'Takım Atanmamış'
    } for person in persons])

if __name__ == '__main__':
    with app.app_context():
        db.init_app(app)
        db.create_all()
        
        # Varsayılan admin kullanıcısı oluştur
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('7905')
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=False, host='127.0.0.1', port=5004)