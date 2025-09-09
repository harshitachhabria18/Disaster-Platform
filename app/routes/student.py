# app/routes/student.py
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('student', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('main.home'))
    return render_template('student/dashboard.html')

@bp.route('/modules')
def modules():
    return render_template('student/modules.html')

@bp.route('/drills')
def drills():
    return render_template('student/drill.html')

@bp.route('/incident')
def incident():
    return render_template('student/incident.html')