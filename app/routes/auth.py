# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Institute

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        institute_id = request.form.get('institute_id')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.role == role:
            if user.role in ['student', 'teacher'] and str(user.institute_id) != institute_id:
                flash('Invalid institute ID', 'error')
                return render_template('auth/login.html')
            
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('govt.dashboard'))
            else:
                return redirect(url_for('main.home'))
        else:
            flash('Login failed. Check your credentials.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        # Process registration form
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        name = f"{first_name} {last_name}"
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        institute_id = request.form.get('institute_id')
        phone = request.form.get('phone')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Check if institute exists for student/teacher roles
        if role in ['student', 'teacher']:
            institute = Institute.query.get(institute_id)
            if not institute:
                flash('Invalid institute ID', 'error')
                return render_template('auth/register.html')
        
        # Create new user
        user = User(
            name=name,
            email=email,
            role=role,
            institute_id=institute_id if role in ['student', 'teacher'] else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))