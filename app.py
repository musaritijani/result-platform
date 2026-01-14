# app.py - Main Flask Application (FIXED VERSION)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration - HARDCODED FOR DEVELOPMENT
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345-hardcoded')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///results.db')

# Fix for Render PostgreSQL URL format
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-12345-hardcoded')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)  # Allow all origins for development

# ==================== MODELS ====================

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    matric = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    matric = db.Column(db.String(50), db.ForeignKey('students.matric'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'matric': self.matric,
            'subject': self.subject,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# ==================== HELPER FUNCTIONS ====================

def log_audit(user_type, user_id, action, details=None):
    """Log user actions for security auditing"""
    try:
        log = AuditLog(user_type=user_type, user_id=user_id, action=action, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Audit log error: {e}")

def validate_score(score):
    """Validate score is within acceptable range"""
    try:
        score_float = float(score)
        return 0 <= score_float <= 100
    except (ValueError, TypeError):
        return False

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register-admin', methods=['POST'])
def register_admin():
    """Register a new admin (in production, this should be protected)"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    admin = Admin(username=data['username'], email=data['email'])
    admin.set_password(data['password'])
    
    db.session.add(admin)
    db.session.commit()
    
    log_audit('system', 'system', f'Admin registered: {data["username"]}')
    
    return jsonify({'message': 'Admin registered successfully'}), 201

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

# ==================== ADMIN ROUTES ====================

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
        return jsonify({'error': 'Matric number already exists'}), 400
    
    if Student.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    student = Student(
        name=data['name'],
        matric=data['matric'],
        email=data['email']
    )
    student.set_password(data['password'])
    
    db.session.add(student)
    db.session.commit()
    
    log_audit('admin', username, f'Registered student: {data["matric"]}')
    
    return jsonify({'message': 'Student registered successfully'}), 201

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
    
    # Validate student exists
    student = Student.query.filter_by(matric=data['matric']).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Validate score
    if not validate_score(data['score']):
        return jsonify({'error': 'Invalid score. Must be between 0 and 100'}), 400
    
    result = Result(
        matric=data['matric'],
        subject=data['subject'],
        score=float(data['score'])
    )
    
    db.session.add(result)
    db.session.commit()
    
    log_audit('admin', username, f'Uploaded result for {data["matric"]} - {data["subject"]}: {data["score"]}')
    
    return jsonify({'message': 'Result uploaded successfully', 'result': result.to_dict()}), 201

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
            return jsonify({'error': 'Invalid score. Must be between 0 and 100'}), 400
        result.score = float(data['score'])
    
    db.session.commit()
    
    log_audit('admin', username, f'Updated result ID {result_id} for {result.matric}')
    
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
    
    matric = result.matric
    subject = result.subject
    
    db.session.delete(result)
    db.session.commit()
    
    log_audit('admin', username, f'Deleted result ID {result_id} for {matric} - {subject}')
    
    return jsonify({'message': 'Result deleted successfully'}), 200

# ==================== STUDENT ROUTES ====================

@app.route('/api/student/results/<matric>', methods=['GET'])
@jwt_required()
def get_student_results(matric):
    """Student endpoint to get their results"""
    current_user = get_jwt_identity()
    role, user_matric = current_user.split(':')
    
    # Students can only view their own results, admins can view any
    if role == 'student' and user_matric != matric:
        return jsonify({'error': 'Unauthorized'}), 403
    
    results = Result.query.filter_by(matric=matric).all()
    
    log_audit(role, user_matric, f'Viewed results for {matric}')
    
    return jsonify({'results': [r.to_dict() for r in results]}), 200

# ==================== PUBLIC ROUTES ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Secure Result Platform API'}), 200

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Secure Result Computation Platform API',
        'version': '1.0.0',
        'security': 'TEE-Enhanced'
    }), 200

# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize the database and create default admin"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if none exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin created: username='admin', password='admin123'")
        
        # Create demo student for testing
        if not Student.query.filter_by(matric='STU001').first():
            student = Student(name='John Doe', matric='STU001', email='john@example.com')
            student.set_password('student123')
            db.session.add(student)
            db.session.commit()
            print("✓ Demo student created: matric='STU001', password='student123'")

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({'error': 'Unprocessable entity - check your request data'}), 422

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("🚀 Secure Result Platform Backend Started!")
    print("="*50)
    print("📍 API Running at: http://localhost:5000")
    print("🏥 Health Check: http://localhost:5000/api/health")
    print("\n👤 Demo Credentials:")
    print("   Admin:   admin / admin123")
    print("   Student: STU001 / student123")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)