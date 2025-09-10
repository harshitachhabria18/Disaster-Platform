# app/routes/student.py
from app import db
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Institute, Student,Module, Drill, DrillParticipation, QuizAttempt, Question, Option, Badge
from datetime import datetime
from flask import request
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import yt_dlp
import PyPDF2
import os
import tempfile
import subprocess
import logging
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

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

@bp.route('/incident')
def incident():
    return render_template('student/incident.html')

@bp.route('/progress')
def progress():
    return render_template('student/progress.html')

@bp.route('/mapgame')
def mapgame():
    return render_template('student/mapgame.html')

@bp.route('/quiz')
def quiz():
    return render_template('student/quiz.html')

@bp.route('/quiz2')
def quiz2():
    return render_template('student/quiz2.html')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Allowed file extensions for PDF upload
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- PDF Text Extraction ----------
def extract_text_from_pdf(pdf_file):
    try:
        logger.info("Extracting text from PDF")
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

# ---------- Helper: Extract video ID ----------
def get_video_id(url):
    try:
        if "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            if "v=" in url:
                return url.split("v=")[-1].split("&")[0]
            elif "youtu.be" in url:
                return url.split("/")[-1]
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return None

# ---------- Step 1: Try Captions ----------
def get_transcript(video_id):
    try:
        logger.info(f"Attempting to get transcript for video ID: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([t["text"] for t in transcript])
        logger.info(f"Successfully retrieved transcript with {len(text)} characters")
        return text
    except TranscriptsDisabled:
        logger.warning("Transcripts disabled for this video")
        return None
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        return None

def transcribe_with_whisper(video_url):
    try:
        logger.info("Starting Whisper transcription")
        # Create a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_path = os.path.join(temp_dir, "audio.%(ext)s")

            # Download audio with yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio_path,
                'quiet': False,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            logger.info("Downloading audio...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Find the downloaded mp3 file
            mp3_file = os.path.join(temp_dir, "audio.mp3")
            
            if not os.path.exists(mp3_file):
                # Try to find the actual file name
                files = os.listdir(temp_dir)
                mp3_files = [f for f in files if f.endswith('.mp3')]
                if mp3_files:
                    mp3_file = os.path.join(temp_dir, mp3_files[0])
                else:
                    raise FileNotFoundError("No MP3 file found after download")

            logger.info(f"Audio file found: {mp3_file}")

            # Transcribe with Groq Whisper
            logger.info("Transcribing with Whisper...")
            with open(mp3_file, "rb") as audio_file:
                transcript = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file
                )

            logger.info("Whisper transcription completed successfully")
            return transcript.text
            
    except Exception as e:
        logger.error(f"Error in Whisper transcription: {e}")
        raise

def summarize_with_groq(text, content_type="video"):
    try:
        logger.info(f"Summarizing {content_type} text with {len(text)} characters")
        
        # Truncate text if it's too long (Groq has token limits)
        if len(text) > 10000:
            text = text[:10000] + "... [truncated for summarization]"
            logger.warning("Text truncated for summarization")
        
        # Different system prompts based on content type
        if content_type == "pdf":
            system_prompt = "You are a helpful assistant that summarizes PDF documents for students and professionals. Provide clear, concise summaries in simple language, highlighting key points and main ideas. Use clear formatting with headings and bullet points but avoid Markdown syntax."
        else:
            system_prompt = "You are a helpful assistant that summarizes video transcripts for students. Provide clear, concise summaries in simple language. Use clear formatting with headings and bullet points but avoid Markdown syntax."
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Please summarize the following {content_type} content:\n\n{text}"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = completion.choices[0].message.content
        logger.info("Summary generated successfully")
        
        # Clean up any Markdown formatting that might have been used
        summary = summary.replace("**", "").replace("*", "• ").replace("#", "")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in summarization: {e}")
        return f"Error generating summary: {str(e)}"


@bp.route("/summarize_video", methods=["POST"])
def summarize_video():
    summary = None
    error = None
    
    video_url = request.form.get("video_url")
    logger.info(f"Processing video URL: {video_url}")
    
    if not video_url:
        error = "Please provide a YouTube URL"
        logger.warning("No URL provided")
    else:
        video_id = get_video_id(video_url)
        
        if not video_id:
            error = "Invalid YouTube URL"
            logger.warning(f"Invalid URL: {video_url}")
        else:
            try:
                # Try captions first
                transcript_text = get_transcript(video_id)

                # If no captions, use whisper
                if not transcript_text:
                    logger.info("No transcript available, using Whisper")
                    transcript_text = transcribe_with_whisper(video_url)
                
                if transcript_text:
                    summary = summarize_with_groq(transcript_text, "video")
                else:
                    error = "Could not retrieve or transcribe video content"
                    logger.error("Failed to get transcript")
                    
            except Exception as e:
                error = f"Error processing video: {str(e)}"
                logger.error(f"Video processing error: {e}")

    return jsonify({"summary": summary, "error": error})

@bp.route("/summarize_pdf", methods=["POST"])
def summarize_pdf():
    summary = None
    error = None
    
    # Check if the post request has the file part
    if 'pdf_file' not in request.files:
        error = "No file uploaded"
        logger.warning("No file uploaded")
        return jsonify({"summary": summary, "error": error})
    
    file = request.files['pdf_file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        error = "No file selected"
        logger.warning("No file selected")
        return jsonify({"summary": summary, "error": error})
    
    if file and allowed_file(file.filename):
        try:
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(file)
            
            if pdf_text and len(pdf_text.strip()) > 0:
                summary = summarize_with_groq(pdf_text, "pdf")
            else:
                error = "Could not extract text from PDF. The file might be scanned or encrypted."
                logger.error("Failed to extract text from PDF")
                
        except Exception as e:
            error = f"Error processing PDF: {str(e)}"
            logger.error(f"PDF processing error: {e}")
    else:
        error = "Invalid file type. Please upload a PDF file."
        logger.warning(f"Invalid file type: {file.filename}")

    return jsonify({"summary": summary, "error": error})
