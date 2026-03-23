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
# MODÈLES – Recrutement
# ════════════════════════════════════════════════════════════════
class JobOffer(db.Model):
    __tablename__ = 'job_offers'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    department  = db.Column(db.String(80))
    contract    = db.Column(db.String(20))
    salary_min  = db.Column(db.Float)
    salary_max  = db.Column(db.Float)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default='open')
    urgent      = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title,
            'department': self.department, 'contract': self.contract,
            'salary_min': self.salary_min, 'salary_max': self.salary_max,
            'description': self.description, 'status': self.status,
            'urgent': self.urgent,
            'created_at': self.created_at.isoformat()
        }

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120))
    phone       = db.Column(db.String(30))
    job_id      = db.Column(db.Integer, db.ForeignKey('job_offers.id'))
    stage       = db.Column(db.String(30), default='sourcing')
    ai_score    = db.Column(db.Integer, default=0)
    notes       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'phone': self.phone, 'job_id': self.job_id,
            'stage': self.stage, 'ai_score': self.ai_score,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

# ════════════════════════════════════════════════════════════════
# ROUTES – Service Recrutement
# ════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    visits = redis_client.incr('visits:app3')
    return jsonify({
        'service': 'Recruitment Microservice - App3',
        'status': 'running',
        'visits': visits
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'app3'})

# ── Job Offers ────────────────────────────────────────────────
@app.route('/jobs', methods=['GET'])
def get_jobs():
    cache_key = 'jobs:all'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    jobs = JobOffer.query.all()
    data = [j.to_dict() for j in jobs]
    redis_client.setex(cache_key, 60, json.dumps(data))
    return jsonify({'data': data, 'source': 'database'})

@app.route('/jobs', methods=['POST'])
def create_job():
    body = request.get_json()
    job = JobOffer(
        title=body['title'],
        department=body.get('department', ''),
        contract=body.get('contract', 'CDI'),
        salary_min=body.get('salary_min', 0),
        salary_max=body.get('salary_max', 0),
        description=body.get('description', ''),
        urgent=body.get('urgent', False)
    )
    db.session.add(job)
    db.session.commit()
    redis_client.delete('jobs:all')
    return jsonify(job.to_dict()), 201

@app.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = JobOffer.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    redis_client.delete('jobs:all')
    return jsonify({'message': f'Job {job_id} deleted'}), 200

# ── Candidates ────────────────────────────────────────────────
@app.route('/candidates', methods=['GET'])
def get_candidates():
    job_id = request.args.get('job_id')
    stage  = request.args.get('stage')
    cache_key = f'candidates:{job_id or "all"}:{stage or "all"}'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify({'data': json.loads(cached), 'source': 'cache'})
    q = Candidate.query
    if job_id:
        q = q.filter_by(job_id=job_id)
    if stage:
        q = q.filter_by(stage=stage)
    candidates = q.all()
    data = [c.to_dict() for c in candidates]
    redis_client.setex(cache_key, 60, json.dumps(data))
    return jsonify({'data': data, 'source': 'database'})

@app.route('/candidates', methods=['POST'])
def create_candidate():
    body = request.get_json()
    candidate = Candidate(
        name=body['name'],
        email=body.get('email', ''),
        phone=body.get('phone', ''),
        job_id=body.get('job_id'),
        stage=body.get('stage', 'sourcing'),
        ai_score=body.get('ai_score', 0),
        notes=body.get('notes', '')
    )
    db.session.add(candidate)
    db.session.commit()
    redis_client.delete('candidates:all:all')
    return jsonify(candidate.to_dict()), 201

@app.route('/candidates/<int:cid>/stage', methods=['PATCH'])
def update_stage(cid):
    candidate = Candidate.query.get_or_404(cid)
    body = request.get_json()
    candidate.stage = body['stage']
    db.session.commit()
    redis_client.delete('candidates:all:all')
    return jsonify(candidate.to_dict())

@app.route('/candidates/<int:cid>', methods=['DELETE'])
def delete_candidate(cid):
    candidate = Candidate.query.get_or_404(cid)
    db.session.delete(candidate)
    db.session.commit()
    redis_client.delete('candidates:all:all')
    return jsonify({'message': f'Candidate {cid} deleted'}), 200

@app.route('/recruitment/stats')
def recruitment_stats():
    stats = {
        'open_jobs': JobOffer.query.filter_by(status='open').count(),
        'total_candidates': Candidate.query.count(),
        'by_stage': {}
    }
    stages = db.session.query(Candidate.stage, db.func.count(Candidate.id))\
                       .group_by(Candidate.stage).all()
    stats['by_stage'] = {s: c for s, c in stages}
    return jsonify({'data': stats})

def seed_data():
    if JobOffer.query.count() == 0:
        jobs = [
            JobOffer(title='Développeur Full Stack', department='IT',
                     contract='CDI', salary_min=2800, salary_max=3500,
                     urgent=True, status='open'),
            JobOffer(title='Data Analyst', department='Finance',
                     contract='CDI', salary_min=3000, salary_max=3800,
                     urgent=False, status='open'),
            JobOffer(title='Commercial B2B', department='Ventes',
                     contract='CDI', salary_min=2500, salary_max=3200,
                     urgent=True, status='open'),
        ]
        db.session.add_all(jobs)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
