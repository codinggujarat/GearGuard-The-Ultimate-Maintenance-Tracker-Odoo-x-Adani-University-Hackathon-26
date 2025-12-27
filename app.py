from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError

# Prevent Flask from loading potentially misencoded global .env files
os.environ["FLASK_SKIP_DOTENV"] = "1"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gearguard-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gearguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='Technician') # Manager, Technician, User
    avatar_url = db.Column(db.String(255))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Electrical, Mechanical, IT, CNC
    description = db.Column(db.String(255))
    equipments = db.relationship('Equipment', backref='category', lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Mechanics, Electricians, IT Support
    members = db.relationship('User', backref='team', lazy=True)
    equipments = db.relationship('Equipment', backref='maintenance_team', lazy=True)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100))
    owner_name = db.Column(db.String(100)) # e.g., "Person name"
    location = db.Column(db.String(100))
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    warranty_info = db.Column(db.String(255))
    is_scrapped = db.Column(db.Boolean, default=False)
    
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    default_technician_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    requests = db.relationship('MaintenanceRequest', backref='equipment', lazy=True)

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False) # Corrective, Preventive
    status = db.Column(db.String(50), default='New') # New, In Progress, Repaired, Scrap
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High
    
    scheduled_date = db.Column(db.DateTime)
    duration = db.Column(db.Float) # Hours spent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50)) # info, warning, success
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='notifications')

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        new_user = User(
            username=username,
            password=generate_password_hash(request.form.get('password')),
            name=request.form.get('name')
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard Route
@app.route('/')
@login_required
def dashboard():
    total_requests = MaintenanceRequest.query.count()
    completed_requests = MaintenanceRequest.query.filter_by(status='Repaired').count()
    resolution_rate = f"{(completed_requests / total_requests * 100):.0f}%" if total_requests > 0 else "100%"
    
    # Overdue = not repaired and older than 3 days (simplified logic for demo)
    from datetime import datetime, timedelta
    overdue_limit = datetime.utcnow() - timedelta(days=3)
    overdue_jobs = MaintenanceRequest.query.filter(MaintenanceRequest.status != 'Repaired', MaintenanceRequest.created_at < overdue_limit).count()

    stats = {
        'total_equipment': Equipment.query.count(),
        'open_requests': MaintenanceRequest.query.filter(MaintenanceRequest.status.in_(['New', 'In Progress'])).count(),
        'overdue_jobs': overdue_jobs,
        'resolution_rate': resolution_rate
    }
    recent_requests = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).limit(5).all()
    teams = Team.query.all()
    return render_template('dashboard.html', stats=stats, recent_requests=recent_requests, teams=teams)

# Equipment Routes
@app.route('/equipment')
@login_required
def equipment_list():
    cat_id = request.args.get('category_id')
    search_query = request.args.get('q')
    
    query = Equipment.query
    if cat_id:
        query = query.filter_by(category_id=cat_id)
        current_cat = Category.query.get(cat_id)
    else:
        current_cat = None
        
    if search_query:
        query = query.filter(
            (Equipment.name.ilike(f'%{search_query}%')) | 
            (Equipment.serial_number.ilike(f'%{search_query}%'))
        )
        
    equipments = query.all()
    categories = Category.query.all()
    return render_template('equipment_list.html', equipments=equipments, categories=categories, current_cat=current_cat, search_query=search_query)

@app.route('/equipment/<int:id>')
@login_required
def equipment_detail(id):
    equipment = Equipment.query.get_or_404(id)
    requests_count = MaintenanceRequest.query.filter_by(equipment_id=id).filter(MaintenanceRequest.status != 'Repaired').count()
    return render_template('equipment_detail.html', equipment=equipment, requests_count=requests_count)

@app.route('/equipment/new', methods=['GET', 'POST'])
@login_required
def new_equipment():
    if request.method == 'POST':
        new_eq = Equipment(
            name=request.form.get('name'),
            serial_number=request.form.get('serial_number'),
            department=request.form.get('department'),
            owner_name=request.form.get('owner_name'),
            location=request.form.get('location'),
            warranty_info=request.form.get('warranty_info'),
            category_id=request.form.get('category_id'),
            team_id=request.form.get('team_id'),
            default_technician_id=request.form.get('technician_id')
        )
        try:
            db.session.add(new_eq)
            db.session.commit()
            flash(f'Asset {new_eq.name} inductions successful', 'success')
            return redirect(url_for('equipment_list'))
        except IntegrityError:
            db.session.rollback()
            flash(f'Error: Serial number {new_eq.serial_number} already exists in the registry.', 'error')
            return redirect(url_for('new_equipment'))
        
    categories = Category.query.all()
    teams = Team.query.all()
    technicians = User.query.filter_by(role='Technician').all()
    return render_template('equipment_form.html', categories=categories, teams=teams, technicians=technicians)

@app.route('/equipment/<int:id>/scrap', methods=['POST'])
def scrap_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    equipment.is_scrapped = True
    db.session.commit()
    return redirect(url_for('equipment_detail', id=id))

@app.route('/equipment/<int:id>/requests')
def equipment_requests(id):
    equipment = Equipment.query.get_or_404(id)
    requests = MaintenanceRequest.query.filter_by(equipment_id=id).all()
    return render_template('requests_list.html', requests=requests, equipment=equipment)

# Request Routes
@app.route('/request/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id')
        subject = request.form.get('subject')
        req_type = request.form.get('type')
        scheduled_date = request.form.get('scheduled_date')
        
        eq = Equipment.query.get(equipment_id)
        new_req = MaintenanceRequest(
            subject=subject,
            equipment_id=equipment_id,
            type=req_type,
            assigned_to_id=eq.default_technician_id,
            scheduled_date=datetime.strptime(scheduled_date, '%Y-%m-%d') if scheduled_date else None
        )
        db.session.add(new_req)
        
        # Create notification for the assigned technician
        if new_req.assigned_to_id:
            notif = Notification(
                title="New Maintenance Request",
                message=f"New request '{subject}' assigned to you for {eq.name}",
                type='info',
                user_id=new_req.assigned_to_id
            )
            db.session.add(notif)
            
        db.session.commit()
        return redirect(url_for('kanban_board'))
        
    equipments = Equipment.query.filter_by(is_scrapped=False).all()
    return render_template('request_form.html', equipments=equipments)

@app.route('/api/equipment/<int:id>')
@login_required
def api_equipment_details(id):
    eq = Equipment.query.get_or_404(id)
    return jsonify({
        'department': eq.department,
        'team_name': eq.maintenance_team.name,
        'category_name': eq.category.name if eq.category else 'N/A',
        'technician': eq.assigned_to.name if eq.assigned_to else 'Default'
    })

# Kanban Board
@app.route('/kanban')
@login_required
def kanban_board():
    requests = MaintenanceRequest.query.all()
    stages = {
        'New': [r for r in requests if r.status == 'New'],
        'In Progress': [r for r in requests if r.status == 'In Progress'],
        'Repaired': [r for r in requests if r.status == 'Repaired'],
        'Scrap': [r for r in requests if r.status == 'Scrap']
    }
    return render_template('kanban.html', stages=stages)

@app.route('/api/request/<int:id>/status', methods=['POST'])
def update_request_status(id):
    data = request.json
    req = MaintenanceRequest.query.get_or_404(id)
    req.status = data.get('status')
    if req.status == 'Scrap':
        req.equipment.is_scrapped = True
    db.session.commit()
    return jsonify({'success': True})

# Calendar View
@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')

@app.route('/api/events')
@login_required
def api_events():
    # Return ALL requests (Preventive + Corrective)
    all_requests = MaintenanceRequest.query.all()
    events = []
    for req in all_requests:
        if req.scheduled_date:
            # Color coding: Red for Corrective, Blue for Preventive
            color = '#ef4444' if req.type == 'Corrective' else '#0ea5e9'
            
            events.append({
                'id': req.id,
                'title': f"{req.equipment.name}: {req.subject}",
                'start': req.scheduled_date.strftime('%Y-%m-%d'),
                'color': color
            })
    return jsonify(events)

# Teams Routes
@app.route('/teams')
@login_required
def teams_list():
    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/teams/<int:id>')
@login_required
def team_manage(id):
    team = Team.query.get_or_404(id)
    all_technicians = User.query.filter_by(role='Technician').all()
    return render_template('team_manage.html', team=team, all_technicians=all_technicians)

@app.route('/teams/<int:id>/update', methods=['POST'])
@login_required
def team_update(id):
    team = Team.query.get_or_404(id)
    team.name = request.form.get('name')
    
    # Update members
    member_ids = request.form.getlist('members')
    # First clear existing members who are NOT in the new list (simplified)
    for member in team.members:
        if str(member.id) not in member_ids:
            member.team_id = None
            
    # Add new members
    for m_id in member_ids:
        user = User.query.get(m_id)
        if user:
            user.team_id = team.id
            
    db.session.commit()
    flash(f'Team {team.name} updated successfully')
    return redirect(url_for('team_manage', id=id))

# Category Route
@app.route('/categories')
@login_required
def categories_list():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

# Analytics API
@app.route('/api/analytics/teams')
@login_required
def api_analytics_teams():
    teams = Team.query.all()
    data = {
        'labels': [t.name for t in teams],
        'counts': [MaintenanceRequest.query.join(Equipment).filter(Equipment.team_id == t.id).count() for t in teams]
    }
    return jsonify(data)

# Notifications API
@app.route('/api/notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%H:%M')
    } for n in notifs])

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return jsonify({'success': True})

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed initial data if empty
        if not Team.query.first():
            # Categories
            it_cat = Category(name='IT Hardware', description='Laptops, Servers, Networking')
            cnc_cat = Category(name='Industrial', description='Machinery and Production tools')
            db.session.add_all([it_cat, cnc_cat])
            db.session.commit()

            it_team = Team(name='IT Support')
            mech_team = Team(name='Mechanics')
            elec_team = Team(name='Electricians')
            db.session.add_all([it_team, mech_team, elec_team])
            db.session.commit()
            
            tech1 = User(username='tech1', password=generate_password_hash('password'), name='Kalp Prajapati', role='Technician', team_id=it_team.id)
            tech2 = User(username='tech2', password=generate_password_hash('password'), name='Krithik Naidu', role='Technician', team_id=mech_team.id)
            manager = User(username='admin', password=generate_password_hash('password'), name='Rishabh', role='Manager')
            db.session.add_all([tech1, tech2, manager])
            db.session.commit()
            
            laptop = Equipment(
                name='MacBook Pro 16', 
                serial_number='SN12345', 
                department='IT', 
                owner_name='Green Swan', 
                location='Workstation 4', 
                team_id=it_team.id,
                category_id=it_cat.id,
                default_technician_id=tech1.id
            )
            cnc = Equipment(
                name='CNC Machine v2', 
                serial_number='SN-CNC-001', 
                department='Production', 
                owner_name='Factory Floor', 
                location='Sector B', 
                team_id=mech_team.id,
                category_id=cnc_cat.id,
                default_technician_id=tech2.id
            )
            db.session.add_all([laptop, cnc])
            db.session.commit()
            
    app.run(debug=True)
