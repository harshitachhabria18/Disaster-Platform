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
     
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    student_class = db.Column(db.String(50), nullable=False)  # e.g., "10th Grade", "B.Tech CSE"
    roll_no = db.Column(db.String(50), nullable=False)
    user = db.relationship("User", backref=db.backref("student", uselist=False))

class Module(db.Model):
    __tablename__ = "modules"
    module_id = db.Column(db.Integer, primary_key=True)  # Primary Key
    title = db.Column(db.String(150), nullable=False)    # Module title
    description = db.Column(db.Text, nullable=True)      # Content / Description
    # db.Enum(...) restricts the column values to a fixed set of choices.
    module_type = db.Column(
        db.Enum("pdf", "video", "text", "game", name="module_type_enum"),
        nullable=False
    )  # Type of module
    region_specific = db.Column(db.Boolean, default=False)  # True if tied to a specific region
    media_link = db.Column(db.String(255), nullable=True)   # Link to file or video
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp
    # Extra fields for frontend display
    page_count = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.String(20), nullable=True)
    duration = db.Column(db.String(20), nullable=True)
    quality = db.Column(db.String(20), nullable=True)

class Drill(db.Model):
    __tablename__ = "drills"
    drill_id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey("institutes.institute_id"))

    # Mode of drill
    drill_type = db.Column(
        db.Enum("virtual", "physical", name="drill_type_enum"),
        nullable=False
    )

    # Type of hazard
    hazard_type = db.Column(
        db.Enum("earthquake", "flood", "fire", "cyclone", "pandemic", name="hazard_type_enum"),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Track status for both modes
    status = db.Column(
        db.Enum("scheduled", "completed", "cancelled", name="drill_status_enum"),
        default="scheduled"
    )
    scheduled_date = db.Column(db.DateTime, nullable=True)

class Badge(db.Model):
    __tablename__ = "badges"
    badge_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # Gold, Silver, Platinum
    description = db.Column(db.String(200))
    icon = db.Column(db.String(255))  # path or URL to badge image

    participations = db.relationship("DrillParticipation", backref="badge", lazy=True)

class DrillParticipation(db.Model):
    __tablename__ = "drill_participation"
    participation_id = db.Column(db.Integer, primary_key=True)
    drill_id = db.Column(db.Integer, db.ForeignKey("drills.drill_id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    score = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.badge_id"), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("drill_id", "user_id", name="uq_user_drill"),
    )

class Question(db.Model):
    __tablename__ = "questions"
    question_id = db.Column(db.Integer, primary_key=True)
    drill_id = db.Column(db.Integer, db.ForeignKey("drills.drill_id"), nullable=True)  # For virtual drills
    hazard_type = db.Column(  
        db.Enum("earthquake", "flood", "fire", "cyclone", "pandemic", name="question_hazard_enum"),
        nullable=True
    )
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(
        db.Enum("quiz", "virtual_drill", "assessment", name="question_type_enum"),
        default="quiz"
    )
    explanation = db.Column(db.Text, nullable=True)  # shown after answering
    # Relationships
    options = db.relationship("Option", backref="question", lazy=True)

class Option(db.Model):
    __tablename__ = "options"
    option_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.question_id"))
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text, nullable=True)  # optional feedback for choice

class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    attempt_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    drill_id = db.Column(db.Integer, db.ForeignKey("drills.drill_id"))  # 🔥 NEW
    hazard_type = db.Column(  # 🔥 NEW
        db.Enum("earthquake", "flood", "fire", "cyclone", "pandemic", name="attempt_hazard_enum"),
        nullable=False
    )
    question_id = db.Column(db.Integer, db.ForeignKey("questions.question_id"))
    selected_option_id = db.Column(db.Integer, db.ForeignKey("options.option_id"))
    score = db.Column(db.Integer, default=0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
