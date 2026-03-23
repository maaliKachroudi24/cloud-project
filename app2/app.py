from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import redis
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql://admin:admin@db:5432/grh'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=True
)

# ════════════════════════════════════════════════════════════════
# MODÈLES – Paie
# ════════════════════════════════════════════════════════════════
class Payslip(db.Model):
    __tablename__ = 'payslips'
    id             = db.Column(db.Integer, primary_key=True)
    employee_id    = db.Column(db.Integer, nullable=False)
    employee_name  = db.Column(db.String(120))
    month          = db.Column(db.String(7))   # YYYY-MM
    gross_salary   = db.Column(db.Float)
    cnss_employee  = db.Column(db.Float)
    cnss_employer  = db.Column(db.Float)
    irpp           = db.Column(db.Float)
    net_salary     = db.Column(db.Float)
    generated_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'month': self.month,
            'gross_salary': self.gross_salary,
            'cnss_employee': self.cnss_employee,
            'cnss_employer': self.cnss_employer,
            'irpp': self.irpp,
            'net_salary': self.net_salary,
            'generated_at': self.generated_at.isoformat()
        }

# ════════════════════════════════════════════════════════════════
# ROUTES – Service Paie
# ════════════════════════════════════════════════════════════════
CNSS_EMPLOYEE_RATE = 0.0918
CNSS_EMPLOYER_RATE = 0.1657
IRPP_RATE          = 0.22

@app.route('/')
def index():
    visits = redis_client.incr('visits:app2')
    return jsonify({
        'service': 'Payroll Microservice - App2',
        'status': 'running',
        'visits': visits
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'app2'})

@app.route('/payslips', methods=['GET'])
def get_payslips():
    month = request.args.get('month')
    cache_key = f'payslips:{month or "all"}'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})

    q = Payslip.query
    if month:
        q = q.filter_by(month=month)
    payslips = q.all()
    data = [p.to_dict() for p in payslips]
    redis_client.setex(cache_key, 60, json.dumps(data))
    return jsonify({'data': data, 'source': 'database'})

@app.route('/payslips/calculate', methods=['POST'])
def calculate_payslip():
    """Calcule et génère une fiche de paie"""
    body = request.get_json()
    gross = float(body['gross_salary'])
    
    cnss_emp  = round(gross * CNSS_EMPLOYEE_RATE, 2)
    cnss_empr = round(gross * CNSS_EMPLOYER_RATE, 2)
    irpp      = round((gross - cnss_emp) * IRPP_RATE, 2)
    net       = round(gross - cnss_emp - irpp, 2)
    
    month = body.get('month', datetime.now().strftime('%Y-%m'))
    
    payslip = Payslip(
        employee_id=body['employee_id'],
        employee_name=body.get('employee_name', ''),
        month=month,
        gross_salary=gross,
        cnss_employee=cnss_emp,
        cnss_employer=cnss_empr,
        irpp=irpp,
        net_salary=net
    )
    db.session.add(payslip)
    db.session.commit()
    redis_client.delete(f'payslips:{month}')
    redis_client.delete('payslips:all')
    redis_client.delete('payroll:stats')
    return jsonify(payslip.to_dict()), 201

@app.route('/payslips/<int:pid>', methods=['DELETE'])
def delete_payslip(pid):
    payslip = Payslip.query.get_or_404(pid)
    db.session.delete(payslip)
    db.session.commit()
    return jsonify({'message': f'Payslip {pid} deleted'}), 200

@app.route('/payroll/stats', methods=['GET'])
def payroll_stats():
    cache_key = 'payroll:stats'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    
    current_month = datetime.now().strftime('%Y-%m')
    payslips = Payslip.query.filter_by(month=current_month).all()
    
    total_gross = sum(p.gross_salary for p in payslips)
    total_net   = sum(p.net_salary for p in payslips)
    total_cnss  = sum(p.cnss_employer for p in payslips)
    
    stats = {
        'month': current_month,
        'count': len(payslips),
        'total_gross': round(total_gross, 2),
        'total_net': round(total_net, 2),
        'total_cnss_employer': round(total_cnss, 2),
        'average_net': round(total_net / len(payslips), 2) if payslips else 0
    }
    redis_client.setex(cache_key, 30, json.dumps(stats))
    return jsonify({'data': stats, 'source': 'database'})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
