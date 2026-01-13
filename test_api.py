"""
Automated API Tests for Secure Result Platform
Run with: pytest test_api.py -v
"""

import pytest
import json
from app import app, db, Admin, Student, Result

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test admin
            admin = Admin(username='testadmin', email='test@admin.com')
            admin.set_password('testpass')
            db.session.add(admin)
            
            # Create test student
            student = Student(name='Test Student', matric='TEST001', email='test@student.com')
            student.set_password('testpass')
            db.session.add(student)
            
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

def get_admin_token(client):
    """Helper to get admin JWT token"""
    response = client.post('/api/auth/login',
        json={'identifier': 'testadmin', 'password': 'testpass', 'role': 'admin'},
        content_type='application/json')
    data = json.loads(response.data)
    return data['access_token']

def get_student_token(client):
    """Helper to get student JWT token"""
    response = client.post('/api/auth/login',
        json={'identifier': 'TEST001', 'password': 'testpass', 'role': 'student'},
        content_type='application/json')
    data = json.loads(response.data)
    return data['access_token']

# ==================== HEALTH CHECK TESTS ====================

def test_health_check(client):
    """Test API health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'Secure Result Computation Platform' in data['message']

# ==================== AUTHENTICATION TESTS ====================

def test_admin_login_success(client):
    """Test successful admin login"""
    response = client.post('/api/auth/login',
        json={'identifier': 'testadmin', 'password': 'testpass', 'role': 'admin'},
        content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert data['role'] == 'admin'

def test_admin_login_failure(client):
    """Test failed admin login"""
    response = client.post('/api/auth/login',
        json={'identifier': 'testadmin', 'password': 'wrongpass', 'role': 'admin'},
        content_type='application/json')
    assert response.status_code == 401

def test_student_login_success(client):
    """Test successful student login"""
    response = client.post('/api/auth/login',
        json={'identifier': 'TEST001', 'password': 'testpass', 'role': 'student'},
        content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert data['role'] == 'student'

def test_missing_credentials(client):
    """Test login with missing credentials"""
    response = client.post('/api/auth/login',
        json={'identifier': 'testadmin'},
        content_type='application/json')
    assert response.status_code == 400

# ==================== ADMIN FUNCTIONALITY TESTS ====================

def test_register_student(client):
    """Test admin can register new student"""
    token = get_admin_token(client)
    response = client.post('/api/admin/students',
        json={
            'name': 'New Student',
            'matric': 'NEW001',
            'email': 'new@student.com',
            'password': 'newpass'
        },
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 201

def test_register_duplicate_student(client):
    """Test registering student with duplicate matric"""
    token = get_admin_token(client)
    response = client.post('/api/admin/students',
        json={
            'name': 'Duplicate Student',
            'matric': 'TEST001',  # Already exists
            'email': 'dup@student.com',
            'password': 'duppass'
        },
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 400

def test_upload_result(client):
    """Test admin can upload result"""
    token = get_admin_token(client)
    response = client.post('/api/admin/results',
        json={
            'matric': 'TEST001',
            'subject': 'Mathematics',
            'score': 85.5
        },
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['result']['subject'] == 'Mathematics'
    assert data['result']['score'] == 85.5

def test_upload_invalid_score(client):
    """Test uploading result with invalid score"""
    token = get_admin_token(client)
    response = client.post('/api/admin/results',
        json={
            'matric': 'TEST001',
            'subject': 'Physics',
            'score': 150  # Invalid - over 100
        },
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 400

def test_upload_result_nonexistent_student(client):
    """Test uploading result for non-existent student"""
    token = get_admin_token(client)
    response = client.post('/api/admin/results',
        json={
            'matric': 'NONEXIST',
            'subject': 'Chemistry',
            'score': 75
        },
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 404

def test_get_all_results(client):
    """Test admin can retrieve all results"""
    token = get_admin_token(client)
    
    # First upload a result
    client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'Math', 'score': 90},
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    
    # Get all results
    response = client.get('/api/admin/results',
        headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['results']) > 0

def test_update_result(client):
    """Test admin can update result"""
    token = get_admin_token(client)
    
    # Upload result
    response = client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'English', 'score': 70},
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    result_id = json.loads(response.data)['result']['id']
    
    # Update result
    response = client.put(f'/api/admin/results/{result_id}',
        json={'score': 85},
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['result']['score'] == 85

def test_delete_result(client):
    """Test admin can delete result"""
    token = get_admin_token(client)
    
    # Upload result
    response = client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'Biology', 'score': 80},
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    result_id = json.loads(response.data)['result']['id']
    
    # Delete result
    response = client.delete(f'/api/admin/results/{result_id}',
        headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get('/api/admin/results',
        headers={'Authorization': f'Bearer {token}'})
    data = json.loads(response.data)
    assert all(r['id'] != result_id for r in data['results'])

# ==================== STUDENT FUNCTIONALITY TESTS ====================

def test_student_view_own_results(client):
    """Test student can view their own results"""
    admin_token = get_admin_token(client)
    student_token = get_student_token(client)
    
    # Admin uploads result
    client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'History', 'score': 78},
        headers={'Authorization': f'Bearer {admin_token}'},
        content_type='application/json')
    
    # Student views results
    response = client.get('/api/student/results/TEST001',
        headers={'Authorization': f'Bearer {student_token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['results']) > 0

def test_student_cannot_view_others_results(client):
    """Test student cannot view other student's results"""
    student_token = get_student_token(client)
    
    # Try to view another student's results
    response = client.get('/api/student/results/OTHER001',
        headers={'Authorization': f'Bearer {student_token}'})
    assert response.status_code == 403

# ==================== AUTHORIZATION TESTS ====================

def test_unauthorized_access_to_admin_endpoint(client):
    """Test unauthorized access to admin endpoints"""
    response = client.get('/api/admin/results')
    assert response.status_code == 401

def test_student_cannot_access_admin_endpoints(client):
    """Test student cannot access admin endpoints"""
    student_token = get_student_token(client)
    
    response = client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'Art', 'score': 88},
        headers={'Authorization': f'Bearer {student_token}'},
        content_type='application/json')
    assert response.status_code == 403

# ==================== SECURITY TESTS ====================

def test_password_hashing(client):
    """Test that passwords are properly hashed"""
    with app.app_context():
        student = Student.query.filter_by(matric='TEST001').first()
        assert student.password_hash != 'testpass'
        assert student.check_password('testpass')
        assert not student.check_password('wrongpass')

def test_audit_logging(client):
    """Test that actions are logged"""
    token = get_admin_token(client)
    
    client.post('/api/admin/results',
        json={'matric': 'TEST001', 'subject': 'Geography', 'score': 82},
        headers={'Authorization': f'Bearer {token}'},
        content_type='application/json')
    
    with app.app_context():
        from app import AuditLog
        logs = AuditLog.query.all()
        assert len(logs) > 0

# ==================== INTEGRATION TESTS ====================

def test_complete_workflow(client):
    """Test complete workflow: register student, upload result, student views"""
    admin_token = get_admin_token(client)
    
    # 1. Admin registers new student
    response = client.post('/api/admin/students',
        json={
            'name': 'Workflow Student',
            'matric': 'WORK001',
            'email': 'work@student.com',
            'password': 'workpass'
        },
        headers={'Authorization': f'Bearer {admin_token}'},
        content_type='application/json')
    assert response.status_code == 201
    
    # 2. Admin uploads results
    subjects = ['Math', 'English', 'Science']
    scores = [85, 90, 78]
    
    for subject, score in zip(subjects, scores):
        response = client.post('/api/admin/results',
            json={'matric': 'WORK001', 'subject': subject, 'score': score},
            headers={'Authorization': f'Bearer {admin_token}'},
            content_type='application/json')
        assert response.status_code == 201
    
    # 3. Student logs in
    response = client.post('/api/auth/login',
        json={'identifier': 'WORK001', 'password': 'workpass', 'role': 'student'},
        content_type='application/json')
    assert response.status_code == 200
    student_token = json.loads(response.data)['access_token']
    
    # 4. Student views results
    response = client.get('/api/student/results/WORK001',
        headers={'Authorization': f'Bearer {student_token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['results']) == 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])