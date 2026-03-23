from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import redis
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ── Configuration Base de données (Partie 2) ──────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://admin:admin@db:5432/grh'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ── Configuration Redis (Partie 3) ───────────────────────────────────
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=True
)

# ════════════════════════════════════════════════════════════════
# MODÈLES (Partie 2 – Base de données)
# ════════════════════════════════════════════════════════════════
class Employee(db.Model):
    __tablename__ = 'employees'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    department  = db.Column(db.String(80))
    role        = db.Column(db.String(80))
    salary      = db.Column(db.Float, default=0)
    contract    = db.Column(db.String(20), default='CDI')
    status      = db.Column(db.String(20), default='Actif')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'role': self.role,
            'salary': self.salary,
            'contract': self.contract,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default='pending')
    priority    = db.Column(db.String(10), default='medium')
    assigned_to = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat()
        }

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    type        = db.Column(db.String(50))
    start_date  = db.Column(db.Date)
    end_date    = db.Column(db.Date)
    status      = db.Column(db.String(20), default='pending')
    reason      = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'type': self.type,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'status': self.status,
            'reason': self.reason
        }

# ════════════════════════════════════════════════════════════════
# PARTIE 1 – API GRH (Fonctionnalités principales)
# ════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    # Compteur de visites Redis (Partie 3)
    visits = redis_client.incr('visits:app1')
    return jsonify({
        'service': 'GRH Microservice - App1',
        'status': 'running',
        'visits': visits,
        'version': '2.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'app1'})

# ── Employees ─────────────────────────────────────────────────
@app.route('/employees', methods=['GET'])
def get_employees():
    cache_key = 'employees:all'
    # Vérifier le cache Redis (Partie 3)
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    
    employees = Employee.query.all()
    data = [e.to_dict() for e in employees]
    
    # Mettre en cache 60 secondes
    redis_client.setex(cache_key, 60, json.dumps(data))
    return jsonify({'data': data, 'source': 'database'})

@app.route('/employees', methods=['POST'])
def create_employee():
    body = request.get_json()
    emp = Employee(
        name=body['name'],
        email=body['email'],
        department=body.get('department', ''),
        role=body.get('role', ''),
        salary=body.get('salary', 0),
        contract=body.get('contract', 'CDI'),
        status=body.get('status', 'Actif')
    )
    db.session.add(emp)
    db.session.commit()
    redis_client.delete('employees:all')  # Invalider le cache
    return jsonify(emp.to_dict()), 201

@app.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    cache_key = f'employee:{emp_id}'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    emp = Employee.query.get_or_404(emp_id)
    redis_client.setex(cache_key, 120, json.dumps(emp.to_dict()))
    return jsonify({'data': emp.to_dict(), 'source': 'database'})

@app.route('/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    body = request.get_json()
    for field in ['name','email','department','role','salary','contract','status']:
        if field in body:
            setattr(emp, field, body[field])
    db.session.commit()
    redis_client.delete('employees:all')
    redis_client.delete(f'employee:{emp_id}')
    return jsonify(emp.to_dict())

@app.route('/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    redis_client.delete('employees:all')
    redis_client.delete(f'employee:{emp_id}')
    return jsonify({'message': f'Employee {emp_id} deleted'}), 200

# ── Tasks (TODO API – Partie 1) ───────────────────────────────
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify({'data': [t.to_dict() for t in tasks]})

@app.route('/tasks', methods=['POST'])
def create_task():
    body = request.get_json()
    task = Task(
        title=body['title'],
        description=body.get('description', ''),
        status=body.get('status', 'pending'),
        priority=body.get('priority', 'medium'),
        assigned_to=body.get('assigned_to')
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': f'Task {task_id} deleted'}), 200

# ── Leave Requests ────────────────────────────────────────────
@app.route('/leaves', methods=['GET'])
def get_leaves():
    leaves = LeaveRequest.query.all()
    return jsonify({'data': [l.to_dict() for l in leaves]})

@app.route('/leaves', methods=['POST'])
def create_leave():
    body = request.get_json()
    leave = LeaveRequest(
        employee_id=body['employee_id'],
        type=body.get('type', 'Congé annuel'),
        start_date=datetime.strptime(body['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(body['end_date'], '%Y-%m-%d').date(),
        reason=body.get('reason', '')
    )
    db.session.add(leave)
    db.session.commit()
    return jsonify(leave.to_dict()), 201

@app.route('/leaves/<int:leave_id>/approve', methods=['PATCH'])
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'approved'
    db.session.commit()
    return jsonify(leave.to_dict())

@app.route('/leaves/<int:leave_id>/reject', methods=['PATCH'])
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = 'rejected'
    db.session.commit()
    return jsonify(leave.to_dict())

# ── Stats / Dashboard ─────────────────────────────────────────
@app.route('/stats', methods=['GET'])
def get_stats():
    cache_key = 'stats:dashboard'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    
    stats = {
        'total_employees': Employee.query.count(),
        'active': Employee.query.filter_by(status='Actif').count(),
        'on_leave': Employee.query.filter_by(status='En congé').count(),
        'pending_leaves': LeaveRequest.query.filter_by(status='pending').count(),
        'open_tasks': Task.query.filter_by(status='pending').count(),
        'departments': {}
    }
    depts = db.session.query(Employee.department, db.func.count(Employee.id))\
                      .group_by(Employee.department).all()
    stats['departments'] = {d: c for d, c in depts}
    
    redis_client.setex(cache_key, 30, json.dumps(stats))
    return jsonify({'data': stats, 'source': 'database'})

# ── Redis visits counter ───────────────────────────────────────
@app.route('/visits')
def get_visits():
    visits = redis_client.get('visits:app1') or 0
    return jsonify({'visits': int(visits)})

# ════════════════════════════════════════════════════════════════
# INIT DB
# ════════════════════════════════════════════════════════════════
def seed_data():
    if Employee.query.count() == 0:
        employees = [
            Employee(name='Amira Ben Salem', email='amira@grh.tn',
                     department='Développement IT', role='Dev Full Stack',
                     salary=3200, contract='CDI', status='Actif'),
            Employee(name='Karim Trabelsi', email='karim@grh.tn',
                     department='Développement IT', role='Chef de Projet',
                     salary=4100, contract='CDI', status='Actif'),
            Employee(name='Sonia Mejri', email='sonia@grh.tn',
                     department='Marketing', role='Responsable Marketing',
                     salary=3600, contract='CDI', status='Actif'),
            Employee(name='Mohamed Gharbi', email='mohamed@grh.tn',
                     department='Finance', role='Analyste Financier',
                     salary=3400, contract='CDI', status='En congé'),
            Employee(name='Leila Hamdi', email='leila@grh.tn',
                     department='Ventes', role='Commercial Senior',
                     salary=2900, contract='CDI', status='Actif'),
        ]
        db.session.add_all(employees)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
