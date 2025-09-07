from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Institute
from app.forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('main.home'))
    
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        role = form.role.data

        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password) and user.role == role:
            # Student: validate institute
            if user.role == 'student' and user.institute_id:
                institute = Institute.query.get(user.institute_id)
                if not institute:
                    flash('Your registered institute does not exist. Contact admin.', 'error')
                    return redirect(url_for('auth.login'))
                
            if user.role == 'teacher' and user.teacher_code:
                institute = Institute.query.get(user.teacher_code)  
                if not institute:
                    flash('Invalid teacher code. Contact admin.', 'error')
                    return redirect(url_for('auth.login'))
                
            login_user(user)

            # Flash message
            if user.role == 'student' and user.institute_id:
                flash(f"Welcome {user.first_name} from {institute.name}!", "success")
            elif user.role == 'teacher':
                flash(f"Welcome {user.first_name}, from {institute.name}!", "success")
            else:
                flash("Login successful!", "success")

            # Redirect based on role
            if user.role == 'student':
                return redirect(url_for('main.home'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('govt.dashboard'))
            else:
                return redirect(url_for('main.home'))
        else:
            flash('Login failed. Check your credentials.', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegisterForm()

    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        name = f"{first_name} {last_name}"
        email = form.email.data
        phone = form.phone.data
        # password = form.password.data
        hashed_password = generate_password_hash(form.password.data)
        role = form.role.data

         # Initialize all role-specific fields as None
        admin_id = None
        institute_id = None
        teacher_code = None

        # Role-specific validation
        if role == 'student':
            try:
                institute_id = int(form.institute_id.data)
            except (ValueError, TypeError):
                flash('Invalid Institute ID', 'error')
                return render_template('auth/register.html', form=form)
            
            institute = Institute.query.get(institute_id)
            if not institute:
                flash('Selected institute does not exist. Please choose a valid one.', 'error')
                return render_template('auth/register.html', form=form)

        elif role == 'teacher':
            teacher_code = form.teacher_code.data
            # Validate teacher code exists as an institute_id
            institute = Institute.query.get(teacher_code)
            if not institute:
                flash('Invalid teacher code. Please use a valid institute ID.', 'error')
                return render_template('auth/register.html', form=form)

        elif role == 'admin':
            admin_id = form.admin_id.data
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            first_name=first_name,
            last_name = last_name,
            email=email,
            phone=phone,
            role=role,
            admin_id=admin_id,
            institute_id=institute_id,
            teacher_code=teacher_code,
            password_hash=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))