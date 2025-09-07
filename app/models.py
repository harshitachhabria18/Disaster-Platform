from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Institute(db.Model):
    __tablename__ = "institutes"
    institute_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))

    # backref="institute" creates a two-way relationship automatically.
    # backref="institute" lets you access user.institute directly without needing an extra relationship in the User model.
    users = db.relationship("User", backref="institute", lazy=True)
    

class User(UserMixin, db.Model):
     __tablename__ = "users"
     id = db.Column(db.Integer, primary_key=True)
     first_name = db.Column(db.String(100), nullable=False)
     last_name = db.Column(db.String(100), nullable=False)
     email = db.Column(db.String(120), unique=True, nullable=False)
     phone = db.Column(db.String(20))
     password_hash = db.Column(db.String(200), nullable=False)
     role = db.Column(db.String(20), nullable=False)
     admin_id = db.Column(db.String(20))
     teacher_code = db.Column(db.String(50))
     institute_id = db.Column(db.Integer, db.ForeignKey("institutes.institute_id"))
    
#     # Relationships
#     quiz_attempts = db.relationship('QuizAttempt', backref='user_ref', lazy=True)
    
#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)
    
#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)
    
#     def get_id(self):
#         return str(self.id)
    
#     # Required for Flask-Login
#     @property
#     def is_active(self):
#         return True
    
#     @property
#     def is_authenticated(self):
#         return True
    
#     @property
#     def is_anonymous(self):
#         return False

# class Module(db.Model):
#     __tablename__ = 'module'
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     description = db.Column(db.Text)
#     grade_level = db.Column(db.String(20))
#     context = db.Column(db.Text)
#     is_system_specific = db.Column(db.Boolean, default=False)
#     resource_link = db.Column(db.String(200))
#     video_url = db.Column(db.String(200))
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     questions = db.relationship('Question', backref='module_ref', lazy=True)

# class Question(db.Model):
#     __tablename__ = 'question'
#     id = db.Column(db.Integer, primary_key=True)
#     module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
#     question_text = db.Column(db.Text, nullable=False)
#     question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false
#     is_critical = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     options = db.relationship('Option', backref='question_ref', lazy=True)
#     quiz_attempts = db.relationship('QuizAttempt', backref='question_ref', lazy=True)

# class Option(db.Model):
#     __tablename__ = 'option'
#     id = db.Column(db.Integer, primary_key=True)
#     question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
#     option_text = db.Column(db.Text, nullable=False)
#     is_correct = db.Column(db.Boolean, default=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

# class QuizAttempt(db.Model):
#     __tablename__ = 'quiz_attempt'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
#     selected_option_id = db.Column(db.Integer, db.ForeignKey('option.id'))
#     score = db.Column(db.Integer, default=0)
#     attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     selected_option = db.relationship('Option', backref='quiz_attempts', foreign_keys=[selected_option_id])

# # User loader function - Moved to __init__.py to avoid circular imports