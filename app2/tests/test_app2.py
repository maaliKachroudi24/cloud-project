"""
tests/test_app2.py – Tests unitaires Microservice 2 (Paie)
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

    from app import app as flask_app, db
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class TestPayroll:
    def test_health(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        assert json.loads(r.data)['service'] == 'app2'

    def test_get_payslips_empty(self, client):
        r = client.get('/payslips')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['data'] == []

    def test_calculate_payslip(self, client):
        payload = {
            'employee_id': 1,
            'employee_name': 'Amira Ben Salem',
            'gross_salary': 3200,
            'month': '2026-03'
        }
        r = client.post('/payslips/calculate',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data['gross_salary'] == 3200
        # CNSS employé = 3200 * 9.18% = 293.76
        assert abs(data['cnss_employee'] - 293.76) < 1
        # Net = brut - cnss_emp - irpp
        assert data['net_salary'] > 0
        assert data['net_salary'] < data['gross_salary']

    def test_payroll_calculation_logic(self, client):
        """Vérifie la logique de calcul CNSS + IRPP"""
        gross = 4000.0
        payload = {
            'employee_id': 2,
            'employee_name': 'Karim Trabelsi',
            'gross_salary': gross,
            'month': '2026-03'
        }
        r = client.post('/payslips/calculate',
                        data=json.dumps(payload),
                        content_type='application/json')
        data = json.loads(r.data)

        cnss_emp  = round(gross * 0.0918, 2)
        cnss_empr = round(gross * 0.1657, 2)
        irpp      = round((gross - cnss_emp) * 0.22, 2)
        net       = round(gross - cnss_emp - irpp, 2)

        assert abs(data['cnss_employee'] - cnss_emp) < 0.01
        assert abs(data['cnss_employer'] - cnss_empr) < 0.01
        assert abs(data['irpp'] - irpp) < 0.01
        assert abs(data['net_salary'] - net) < 0.01

    def test_payroll_stats(self, client):
        r = client.get('/payroll/stats')
        assert r.status_code == 200
        data = json.loads(r.data)['data']
        assert 'total_gross' in data
        assert 'total_net' in data
        assert 'count' in data

    def test_delete_payslip(self, client):
        payload = {'employee_id': 3, 'employee_name': 'Test',
                   'gross_salary': 2500, 'month': '2026-03'}
        r = client.post('/payslips/calculate',
                        data=json.dumps(payload),
                        content_type='application/json')
        pid = json.loads(r.data)['id']

        r = client.delete(f'/payslips/{pid}')
        assert r.status_code == 200

    def test_filter_payslips_by_month(self, client):
        # Créer deux fiches sur des mois différents
        for month, emp in [('2026-02', 10), ('2026-03', 11)]:
            client.post('/payslips/calculate',
                        data=json.dumps({'employee_id': emp,
                                         'employee_name': f'Emp {emp}',
                                         'gross_salary': 3000,
                                         'month': month}),
                        content_type='application/json')

        r = client.get('/payslips?month=2026-02')
        assert r.status_code == 200
        data = json.loads(r.data)['data']
        assert all(p['month'] == '2026-02' for p in data)
