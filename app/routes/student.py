# app/routes/student.py
from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user

bp = Blueprint('student', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('main.home'))
    return render_template('student/dashboard.html')