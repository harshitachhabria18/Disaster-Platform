# app/routes/teacher.py
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('teacher', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('main.home'))
    return render_template('teacher/dashboard.html')