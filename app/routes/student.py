# app/routes/student.py
from app import db
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Institute, Student,Module, Drill, DrillParticipation, QuizAttempt, Question, Option, Badge
from datetime import datetime

bp = Blueprint('student', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.login"))
    
    return render_template(
        "student/dashboard.html",
        student_name=current_user.first_name,
        student_grade=student.student_class,
        roll_no=student.roll_no
    )

@bp.route('/modules')
def modules():
    modules = Module.query.all()  # fetch all modules
    latest_modules = Module.query.order_by(Module.created_at.desc()).limit(3).all()
    return render_template('student/modules.html', modules=modules, latest_modules=latest_modules)

@bp.route('/drills', methods=["GET","POST"])
def drills():
    # Get the student's profile
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.login"))
    
    # Fetch drills for this student's institute
    drills_list = Drill.query.filter_by(institute_id=current_user.institute_id)\
                             .order_by(Drill.scheduled_date.asc()).all()
    
    # Fetching virtual and physical drills
    virtual_drills = []
    for drill in drills_list:
        if drill.drill_type == "virtual":
            # Load questions and options for this drill
            drill.questions = Question.query.filter_by(drill_id=drill.drill_id).all()
            for q in drill.questions:
                q.options = Option.query.filter_by(question_id=q.question_id).all()
            virtual_drills.append(drill)

    # virtual_drills = [d for d in drills_list if d.drill_type == "virtual"]
    physical_drills = [d for d in drills_list if d.drill_type == "physical"]

    # Fetch existing participations and badges
    participations = DrillParticipation.query.filter_by(user_id=current_user.id).all()
    completed_drills = {p.drill_id: p for p in participations if p.completed_at is not None}
    badges = Badge.query.join(DrillParticipation).filter(DrillParticipation.user_id == current_user.id).all()

    results = None  # To pass score/badge info to template

    if request.method == "POST":
        drill_id = int(request.form.get("drill_id"))
        drill = Drill.query.get_or_404(drill_id)

        # Calculate score
        questions = Question.query.filter_by(drill_id=drill_id).all()
        score = 0
        for q in questions:
            selected_option_id = request.form.get(f"question_{q.question_id}")
            if selected_option_id:
                option = Option.query.get(int(selected_option_id))
                if option and option.is_correct:
                    score += 1

        # Save DrillParticipation
        participation = DrillParticipation.query.filter_by(
            user_id=current_user.id,
            drill_id=drill_id
        ).first()
        if not participation:
            participation = DrillParticipation(
                user_id=current_user.id,
                drill_id=drill_id,
                score=score,
                completed_at=datetime.utcnow()
            )
            db.session.add(participation)
        else:
            participation.score = score
            participation.completed_at = datetime.utcnow()

        # Assign badges based on score
        badges_awarded = []
        badge = None
        if score >= 5:
            badge = Badge.query.filter_by(name="Gold").first()
        elif score >= 3:
            badge = Badge.query.filter_by(name="Silver").first()

        if badge:
            participation.badge_id = badge.badge_id
            badges_awarded.append(badge.name)

        db.session.commit()

        # Pass results to template & flash message
        results = {
            "drill_title": drill.title,
            "score": score,
            "badges_awarded": badges_awarded
        }
        flash(f"Drill Completed! Score: {score}, Badges Earned: {', '.join(badges_awarded) if badges_awarded else 'None'}", "success")

    return render_template(
        "student/drill.html",
        virtual_drills=virtual_drills,
        physical_drills=physical_drills,
        completed_drills=completed_drills,
        badges=badges,
        results=results
    )
