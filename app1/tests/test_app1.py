"""
tests/test_app1.py – Tests unitaires Microservice 1 (Employees / Tasks / Leaves)
Partie 5 – CI/CD : ces tests sont exécutés dans le pipeline GitHub Actions
"""
import pytest
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Fixtures ──────────────────────────────────────────────────
@pytest.fixture
def app():
    """Crée une instance Flask de test avec SQLite en mémoire"""
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

# ── Tests root ────────────────────────────────────────────────
class TestRoot:
    def test_index(self, client):
        r = client.get('/')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['service'] == 'GRH Microservice - App1'
        assert data['status'] == 'running'

    def test_health(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'app1'

# ── Tests Employees ───────────────────────────────────────────
class TestEmployees:
    def test_get_employees(self, client):
        r = client.get('/employees')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'data' in data

    def test_create_employee(self, client):
        payload = {
            'name': 'Test Employé',
            'email': 'test@grh.tn',
            'department': 'IT',
            'role': 'Développeur',
            'salary': 3000,
            'contract': 'CDI'
        }
        r = client.post('/employees',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['name'] == 'Test Employé'
        assert data['email'] == 'test@grh.tn'
        assert data['salary'] == 3000

    def test_get_employee_by_id(self, client):
        # Créer d'abord
        payload = {'name': 'Amira Test', 'email': 'amira.test@grh.tn',
                   'department': 'Finance', 'salary': 3200}
        r = client.post('/employees',
                        data=json.dumps(payload),
                        content_type='application/json')
        emp_id = json.loads(r.data)['id']

        # Récupérer
        r = client.get(f'/employees/{emp_id}')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['data']['name'] == 'Amira Test'

    def test_update_employee(self, client):
        payload = {'name': 'Update Test', 'email': 'update@grh.tn', 'salary': 2800}
        r = client.post('/employees',
                        data=json.dumps(payload),
                        content_type='application/json')
        emp_id = json.loads(r.data)['id']

        update = {'salary': 3500, 'status': 'En congé'}
        r = client.put(f'/employees/{emp_id}',
                       data=json.dumps(update),
                       content_type='application/json')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['salary'] == 3500
        assert data['status'] == 'En congé'

    def test_delete_employee(self, client):
        payload = {'name': 'Delete Me', 'email': 'delete@grh.tn', 'salary': 2500}
        r = client.post('/employees',
                        data=json.dumps(payload),
                        content_type='application/json')
        emp_id = json.loads(r.data)['id']

        r = client.delete(f'/employees/{emp_id}')
        assert r.status_code == 200

        r = client.get(f'/employees/{emp_id}')
        assert r.status_code == 404

    def test_employee_not_found(self, client):
        r = client.get('/employees/99999')
        assert r.status_code == 404

# ── Tests Tasks (Partie 1 – TODO API) ────────────────────────
class TestTasks:
    def test_get_tasks(self, client):
        r = client.get('/tasks')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'data' in data

    def test_create_task(self, client):
        payload = {
            'title': 'Réviser les contrats Q2',
            'description': 'Vérifier tous les CDD expirant en Q2',
            'priority': 'high',
            'status': 'pending'
        }
        r = client.post('/tasks',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['title'] == 'Réviser les contrats Q2'
        assert data['priority'] == 'high'

    def test_delete_task(self, client):
        payload = {'title': 'Tâche à supprimer', 'priority': 'low'}
        r = client.post('/tasks',
                        data=json.dumps(payload),
                        content_type='application/json')
        task_id = json.loads(r.data)['id']

        r = client.delete(f'/tasks/{task_id}')
        assert r.status_code == 200

    def test_task_required_fields(self, client):
        r = client.post('/tasks',
                        data=json.dumps({}),
                        content_type='application/json')
        assert r.status_code in [400, 500]  # Erreur attendue sans titre

# ── Tests Leave Requests ──────────────────────────────────────
class TestLeaves:
    def _create_employee(self, client):
        r = client.post('/employees',
                        data=json.dumps({'name': 'Congé Test',
                                         'email': 'conge@grh.tn',
                                         'salary': 3000}),
                        content_type='application/json')
        return json.loads(r.data)['id']

    def test_get_leaves(self, client):
        r = client.get('/leaves')
        assert r.status_code == 200

    def test_create_leave(self, client):
        emp_id = self._create_employee(client)
        payload = {
            'employee_id': emp_id,
            'type': 'Congé annuel',
            'start_date': '2026-04-01',
            'end_date': '2026-04-05',
            'reason': 'Vacances'
        }
        r = client.post('/leaves',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['status'] == 'pending'
        assert data['type'] == 'Congé annuel'

    def test_approve_leave(self, client):
        emp_id = self._create_employee(client)
        payload = {'employee_id': emp_id, 'type': 'Congé maladie',
                   'start_date': '2026-04-10', 'end_date': '2026-04-11'}
        r = client.post('/leaves',
                        data=json.dumps(payload),
                        content_type='application/json')
        leave_id = json.loads(r.data)['id']

        r = client.patch(f'/leaves/{leave_id}/approve')
        assert r.status_code == 200
        assert json.loads(r.data)['status'] == 'approved'

    def test_reject_leave(self, client):
        emp_id = self._create_employee(client)
        payload = {'employee_id': emp_id, 'type': 'Congé sans solde',
                   'start_date': '2026-05-01', 'end_date': '2026-05-03'}
        r = client.post('/leaves',
                        data=json.dumps(payload),
                        content_type='application/json')
        leave_id = json.loads(r.data)['id']

        r = client.patch(f'/leaves/{leave_id}/reject')
        assert r.status_code == 200
        assert json.loads(r.data)['status'] == 'rejected'

# ── Tests Stats ───────────────────────────────────────────────
class TestStats:
    def test_stats(self, client):
        r = client.get('/stats')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'total_employees' in data['data']
        assert 'active' in data['data']
        assert 'pending_leaves' in data['data']

    def test_visits(self, client):
        r = client.get('/visits')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'visits' in data
