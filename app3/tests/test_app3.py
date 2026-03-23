"""
tests/test_app3.py – Tests unitaires Microservice 3 (Recrutement)
"""
import pytest
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['REDIS_HOST']   = 'localhost'
    os.environ['REDIS_PORT']   = '6379'

    from app import app as flask_app, db, seed_data
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.app_context():
        db.create_all()
        try:
            seed_data()
        except Exception:
            pass
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class TestJobs:
    def test_health(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        assert json.loads(r.data)['service'] == 'app3'

    def test_get_jobs(self, client):
        r = client.get('/jobs')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'data' in data
        assert len(data['data']) >= 3  # Données seed

    def test_create_job(self, client):
        payload = {
            'title': 'DevOps Engineer',
            'department': 'IT',
            'contract': 'CDI',
            'salary_min': 3500,
            'salary_max': 4500,
            'description': 'Maîtrise Docker et Kubernetes',
            'urgent': True
        }
        r = client.post('/jobs',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['title'] == 'DevOps Engineer'
        assert data['urgent'] is True
        assert data['status'] == 'open'

    def test_delete_job(self, client):
        payload = {'title': 'Poste à supprimer', 'department': 'Test'}
        r = client.post('/jobs',
                        data=json.dumps(payload),
                        content_type='application/json')
        job_id = json.loads(r.data)['id']

        r = client.delete(f'/jobs/{job_id}')
        assert r.status_code == 200

class TestCandidates:
    def _create_job(self, client):
        r = client.post('/jobs',
                        data=json.dumps({'title': 'Test Job', 'department': 'IT'}),
                        content_type='application/json')
        return json.loads(r.data)['id']

    def test_get_candidates(self, client):
        r = client.get('/candidates')
        assert r.status_code == 200

    def test_create_candidate(self, client):
        job_id = self._create_job(client)
        payload = {
            'name': 'Sara Zouari',
            'email': 'sara@mail.tn',
            'phone': '+216 55 123 456',
            'job_id': job_id,
            'stage': 'sourcing',
            'ai_score': 85,
            'notes': 'Profil solide, expérience React/Node'
        }
        r = client.post('/candidates',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['name'] == 'Sara Zouari'
        assert data['ai_score'] == 85
        assert data['stage'] == 'sourcing'

    def test_update_candidate_stage(self, client):
        job_id = self._create_job(client)
        r = client.post('/candidates',
                        data=json.dumps({'name': 'Pipeline Test',
                                         'email': 'pipeline@test.tn',
                                         'job_id': job_id,
                                         'stage': 'sourcing'}),
                        content_type='application/json')
        cid = json.loads(r.data)['id']

        # Avancer dans le pipeline
        stages = ['cv_received', 'phone_interview', 'hr_interview', 'offer']
        for stage in stages:
            r = client.patch(f'/candidates/{cid}/stage',
                             data=json.dumps({'stage': stage}),
                             content_type='application/json')
            assert r.status_code == 200
            assert json.loads(r.data)['stage'] == stage

    def test_filter_candidates_by_job(self, client):
        job_id = self._create_job(client)
        # Créer 2 candidats pour ce poste
        for name in ['Candidat A', 'Candidat B']:
            client.post('/candidates',
                        data=json.dumps({'name': name,
                                         'email': f'{name.lower().replace(" ","")}@test.tn',
                                         'job_id': job_id}),
                        content_type='application/json')

        r = client.get(f'/candidates?job_id={job_id}')
        assert r.status_code == 200
        data = json.loads(r.data)['data']
        assert len(data) == 2

    def test_delete_candidate(self, client):
        r = client.post('/candidates',
                        data=json.dumps({'name': 'Delete Me',
                                         'email': 'deleteme@test.tn'}),
                        content_type='application/json')
        cid = json.loads(r.data)['id']

        r = client.delete(f'/candidates/{cid}')
        assert r.status_code == 200

class TestRecruitmentStats:
    def test_recruitment_stats(self, client):
        r = client.get('/recruitment/stats')
        assert r.status_code == 200
        data = json.loads(r.data)['data']
        assert 'open_jobs' in data
        assert 'total_candidates' in data
        assert 'by_stage' in data
