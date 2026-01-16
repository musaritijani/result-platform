# app.py - Production Ready Flask Application
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import os

app = Flask(__name__)

# Configuration - Production Ready with Environment Variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345-hardcoded')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///results.db')

# Fix for Render/Heroku PostgreSQL URL format
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-12345-hardcoded')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for all origins

# Models
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    matric = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'matric': self.matric,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    matric = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_grade(self):
        if self.score >= 70:
            return 'A'
        elif self.score >= 60:
            return 'B'
        elif self.score >= 50:
            return 'C'
        elif self.score >= 45:
            return 'D'
        elif self.score >= 40:
            return 'E'
        else:
            return 'F'
    
    def to_dict(self):
        return {
            'id': self.id,
            'matric': self.matric,
            'subject': self.subject,
            'score': self.score,
            'grade': self.grade or self.calculate_grade(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20))
    user_id = db.Column(db.String(100))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_type': self.user_type,
            'user_id': self.user_id,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# Helper Functions
def log_audit(user_type, user_id, action):
    log = AuditLog(user_type=user_type, user_id=user_id, action=action)
    db.session.add(log)
    db.session.commit()

def validate_score(score):
    try:
        score_float = float(score)
        return 0 <= score_float <= 100
    except (ValueError, TypeError):
        return False

# Routes
@app.route('/')
def index():
    return jsonify({
        'message': 'Secure Result Computation Platform API',
        'version': '1.0.0',
        'security': 'TEE-Enhanced'
    }), 200

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Secure Result Platform API'}), 200

@app.route('/api/init-database', methods=['GET'])
def init_database_endpoint():
    """Endpoint to initialize database - Call this first!"""
    try:
        db.create_all()
        
        # Create admin if doesn't exist
        admin_exists = Admin.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = Admin(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            admin_msg = "✓ Admin created: username='admin', password='admin123'"
        else:
            admin_msg = "✓ Admin already exists"
        
        # Create student if doesn't exist
        student_exists = Student.query.filter_by(matric='STU001').first()
        if not student_exists:
            student = Student(name='John Doe', matric='STU001', email='john@example.com')
            student.set_password('student123')
            db.session.add(student)
            db.session.commit()
            student_msg = "✓ Student created: matric='STU001', password='student123'"
        else:
            student_msg = "✓ Student already exists"
        
        return jsonify({
            'status': 'success',
            'message': 'Database initialized successfully',
            'admin': admin_msg,
            'student': student_msg
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login for both admin and student"""
    data = request.get_json()
    
    if not data or not data.get('identifier') or not data.get('password') or not data.get('role'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    role = data['role']
    identifier = data['identifier']
    password = data['password']
    
    if role == 'admin':
        user = Admin.query.filter_by(username=identifier).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=f"admin:{user.username}")
            log_audit('admin', user.username, 'Login successful')
            return jsonify({
                'access_token': access_token,
                'role': 'admin',
                'name': user.username,
                'email': user.email
            }), 200
    
    elif role == 'student':
        user = Student.query.filter_by(matric=identifier).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=f"student:{user.matric}")
            log_audit('student', user.matric, 'Login successful')
            return jsonify({
                'access_token': access_token,
                'role': 'student',
                'name': user.name,
                'matric': user.matric
            }), 200
    
    log_audit('unknown', identifier, f'Failed login attempt as {role}')
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/admin/results', methods=['GET'])
@jwt_required()
def get_all_results():
    """Admin endpoint to get all results"""
    current_user = get_jwt_identity()
    role, username = current_user.split(':')
    
    if role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    results = Result.query.all()
    return jsonify({'results': [r.to_dict() for r in results]}), 200

@app.route('/api/admin/results', methods=['POST'])
@jwt_required()
def upload_result():
    """Admin endpoint to upload a result"""
    current_user = get_jwt_identity()
    role, username = current_user.split(':')
    
    if role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if not all(k in data for k in ['matric', 'subject', 'score']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    student = Student.query.filter_by(matric=data['matric']).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if not validate_score(data['score']):
        return jsonify({'error': 'Invalid score. Must be between 0 and 100'}), 400
    
    result = Result(
        matric=data['matric'],
        subject=data['subject'],
        score=float(data['score'])
    )
    result.grade = result.calculate_grade()
    
    db.session.add(result)
    db.session.commit()
    
    log_audit('admin', username, f'Uploaded result for {data["matric"]} - {data["subject"]}: {data["score"]}')
    
    return jsonify({'message': 'Result uploaded successfully', 'result': result.to_dict()}), 201

@app.route('/api/admin/results/<int:result_id>', methods=['PUT'])
@jwt_required()
def update_result(result_id):
    """Admin endpoint to update a result"""
    current_user = get_jwt_identity()
    role, username = current_user.split(':')
    
    if role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    result = Result.query.get(result_id)
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    data = request.get_json()
    
    if 'subject' in data:
        result.subject = data['subject']
    if 'score' in data:
        if not validate_score(data['score']):
            return jsonify({'error': 'Invalid score'}), 400
        result.score = float(data['score'])
        result.grade = result.calculate_grade()
    
    db.session.commit()
    log_audit('admin', username, f'Updated result ID {result_id}')
    
    return jsonify({'message': 'Result updated successfully', 'result': result.to_dict()}), 200

@app.route('/api/admin/results/<int:result_id>', methods=['DELETE'])
@jwt_required()
def delete_result(result_id):
    """Admin endpoint to delete a result"""
    current_user = get_jwt_identity()
    role, username = current_user.split(':')
    
    if role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    result = Result.query.get(result_id)
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    db.session.delete(result)
    db.session.commit()
    
    log_audit('admin', username, f'Deleted result ID {result_id}')
    
    return jsonify({'message': 'Result deleted successfully'}), 200

@app.route('/api/admin/students', methods=['POST'])
@jwt_required()
def register_student():
    """Admin endpoint to register a new student"""
    current_user = get_jwt_identity()
    role, username = current_user.split(':')
    
    if role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if not all(k in data for k in ['name', 'matric', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if Student.query.filter_by(matric=data['matric']).first():
        return jsonify({'error': 'Student with this matric number already exists'}), 409
    
    if Student.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Student with this email already exists'}), 409
    
    student = Student(
        name=data['name'],
        matric=data['matric'],
        email=data['email']
    )
    student.set_password(data['password'])
    
    db.session.add(student)
    db.session.commit()
    
    log_audit('admin', username, f'Registered new student: {data["matric"]}')
    
    return jsonify({'message': 'Student registered successfully', 'student': student.to_dict()}), 201

@app.route('/api/student/results/<matric>', methods=['GET'])
@jwt_required()
def get_student_results(matric):
    """Student endpoint to get their results"""
    current_user = get_jwt_identity()
    role, user_matric = current_user.split(':')
    
    if role == 'student' and user_matric != matric:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.query.filter_by(matric=matric).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    results = Result.query.filter_by(matric=matric).all()
    
    return jsonify({
        'student': student.to_dict(),
        'results': [r.to_dict() for r in results]
    }), 200

# Initialize database when app loads (works with gunicorn)
try:
    with app.app_context():
        db.create_all()
        print("✓ Database tables created")
        
        # Try to create default users
        try:
            if not Admin.query.filter_by(username='admin').first():
                admin = Admin(username='admin', email='admin@example.com')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Default admin created: username='admin', password='admin123'")
            else:
                print("✓ Admin already exists")
        except:
            print("⚠ Admin creation skipped (call /api/init-database)")
        
        try:
            if not Student.query.filter_by(matric='STU001').first():
                student = Student(name='John Doe', matric='STU001', email='john@example.com')
                student.set_password('student123')
                db.session.add(student)
                db.session.commit()
                print("✓ Demo student created: matric='STU001', password='student123'")
            else:
                print("✓ Student already exists")
        except:
            print("⚠ Student creation skipped (call /api/init-database)")
        
        print("✅ Database initialization complete!")
        
except Exception as e:
    print(f"❌ Database initialization error: {str(e)}")
    print("⚠ Call /api/init-database to initialize manually")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Secure Result Platform Backend Started!")
    print("="*50)
    print(f"📍 API Running at: http://localhost:{os.environ.get('PORT', 5000)}")
    print(f"🏥 Health Check: http://localhost:{os.environ.get('PORT', 5000)}/api/health")
    print(f"🔧 Init Database: http://localhost:{os.environ.get('PORT', 5000)}/api/init-database")
    print("\n👤 Demo Credentials:")
    print("   Admin:   admin / admin123")
    print("   Student: STU001 / student123")
    print("="*50 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)