from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
import re
from app.models import User, Institute

# Password validation
def validate_password(form, field):
    password = field.data
    if (not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        raise ValidationError(
            "Password must contain an uppercase, lowercase, number, and special character."
        )

# Unique email validation
def validate_email_unique(form, field):
    if User.query.filter_by(email=field.data).first():
        raise ValidationError("Email already registered.")

# Role-specific validations  
def validate_student_id(form, field):
    if form.role.data == 'student' and not field.data:
        raise ValidationError("Institute ID is required for students.")

def validate_teacher_code(form, field):
    if form.role.data == 'teacher' and not field.data:
        raise ValidationError("Teacher Code is required for teachers.")

def validate_admin_id(form, field):
    if form.role.data == 'admin' and not field.data:
        raise ValidationError("Administrator ID is required.")

def validate_student_class(form, field):
    if form.role.data == 'student' and not field.data:
        raise ValidationError("Class is required for students.")

def validate_roll_no(form, field):
    if form.role.data == 'student' and not field.data:
        raise ValidationError("Roll number is required for students.")


class RegisterForm(FlaskForm):
    role = SelectField(
        'Role*',
        choices=[
            ('', 'Select Role'), 
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('admin', 'Administrator')
        ],
        validators=[DataRequired()]
    )
    first_name = StringField('First Name*', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name*', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address*', validators=[DataRequired(), Email(), validate_email_unique])
    # Role-specific IDs
    institute_id = StringField('Institute ID', validators=[validate_student_id])
    teacher_code = StringField('Teacher Code', validators=[validate_teacher_code])
    admin_id = StringField('Administrator ID', validators=[validate_admin_id])

    # new student fields
    student_class = StringField('Class', validators=[validate_student_class])
    roll_no = StringField('Roll Number', validators=[validate_roll_no])

    phone = StringField(
        'Phone Number*',
        validators=[
            DataRequired(),
            Regexp(r'^(?:\+91)?[6-9]\d{9}$', message="Enter a valid 10-digit Indian phone number.")
        ]
    )
    password = PasswordField('Password*', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters."),
        validate_password
    ])
    confirm_password = PasswordField('Confirm Password*', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    terms = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])
    submit = SubmitField('Create Account')

# login form
class LoginForm(FlaskForm):
    email = StringField(
        'Email Address',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    role = SelectField(
        'Role',
        choices=[
            ('', 'Select Role'),
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('admin', 'Administrator')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Sign In')
