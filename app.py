"""
AI Interview Coach — Main Flask Application
=============================================
Production-level Flask app with modular architecture.
Routes: Auth, Resume Upload, Written Test, Interview Simulation, Report.
"""

import os
import json
import random
import secrets
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)

# Local modules
from resume_parser import parse_pdf, parse_text, extract_profile
from evaluator import evaluate_full_test, evaluate_interview_answer
from interview_engine import InterviewSession
from scorer import (
    calculate_technical_score, calculate_communication_score,
    generate_recommendation, generate_report
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# In-memory user store (demo/capstone — use a DB in production)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# Active interview sessions keyed by username
INTERVIEW_SESSIONS = {}

# Role mapping for question lookup
ROLE_MAP = {
    "ai_engineer": "AI Engineer",
    "backend_engineer": "Backend Engineer",
    "frontend_engineer": "Frontend Engineer",
    "data_scientist": "Data Scientist",
    "data_analyst": "Data Analyst",
    "ml_engineer": "ML Engineer",
    "full_stack_developer": "Full Stack Developer",
    "devops_engineer": "DevOps Engineer",
    "cybersecurity_engineer": "Cybersecurity Engineer",
    "software_engineer": "Software Engineer",
    "ux_engineer": "UX Engineer",
    "ui_engineer": "UI Engineer"
}


def _load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _load_questions():
    qpath = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(qpath, "r") as f:
        return json.load(f)


def _current_user():
    return session.get("username")


# ---------------------------------------------------------------------------
# Routes — Auth
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", user=_current_user())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = _load_users()

        if username in users and users[username]["password"] == password:
            session["username"] = username
            flash("Welcome back!", "success")
            return redirect(url_for("upload_resume"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip()

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for("login"))

    users = _load_users()
    if username in users:
        flash("Username already exists.", "error")
        return redirect(url_for("login"))

    users[username] = {"password": password, "email": email}
    _save_users(users)
    session["username"] = username
    flash("Account created successfully!", "success")
    return redirect(url_for("upload_resume"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Routes — Resume Upload & Analysis
# ---------------------------------------------------------------------------

@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():
    if not _current_user():
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        resume_text = ""

        # Handle file upload
        if "resume_file" in request.files:
            file = request.files["resume_file"]
            if file and file.filename:
                if file.filename.endswith(".pdf"):
                    resume_text = parse_pdf(file)
                else:
                    resume_text = file.read().decode("utf-8", errors="ignore")

        # Handle text paste (fallback)
        if not resume_text:
            resume_text = request.form.get("resume_text", "").strip()

        if not resume_text:
            flash("Please upload a resume file or paste your resume text.", "error")
            return redirect(url_for("upload_resume"))

        # Extract profile
        profile = extract_profile(resume_text)
        session["profile"] = profile
        session["resume_text"] = resume_text[:5000]  # Cap stored text

        return render_template("upload_resume.html",
                               user=_current_user(),
                               profile=profile,
                               show_results=True)

    return render_template("upload_resume.html",
                           user=_current_user(),
                           profile=None,
                           show_results=False)


# ---------------------------------------------------------------------------
# Routes — Role Selection & Written Test
# ---------------------------------------------------------------------------

@app.route("/roles")
def roles():
    if not _current_user():
        flash("Please login first.", "error")
        return redirect(url_for("login"))
    return render_template("role_select.html", user=_current_user())


@app.route("/difficulty")
def difficulty():
    role = request.args.get("role", "")
    return render_template("difficulty.html", role=role, user=_current_user())


@app.route("/technical")
def technical():
    if not _current_user():
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    role_key = request.args.get("role", "")
    level = request.args.get("level", "easy")
    time_limit = int(request.args.get("time", 300))

    role_display = ROLE_MAP.get(role_key, role_key.replace("_", " "))

    data = _load_questions()
    questions = data.get(role_display, {}).get(level, [])

    # Mix in aptitude questions
    aptitude = data.get("Aptitude", {})
    apt_quant = aptitude.get("quantitative", [])
    apt_logic = aptitude.get("logical", [])
    aptitude_mix = random.sample(apt_quant, min(3, len(apt_quant))) + \
                   random.sample(apt_logic, min(2, len(apt_logic)))

    all_questions = aptitude_mix + questions
    if len(all_questions) > 15:
        # Keep all aptitude, sample from technical
        tech_sample = random.sample(questions, min(10, len(questions)))
        all_questions = aptitude_mix + tech_sample

    # Store in session for grading
    session["test_questions"] = all_questions
    session["test_role"] = role_display
    session["test_level"] = level

    return render_template("tech_test.html",
                           questions=all_questions,
                           time=time_limit,
                           role=role_display,
                           level=level,
                           user=_current_user())


@app.route("/submit_test", methods=["POST"])
def submit_test():
    questions = session.get("test_questions", [])
    user_answers = request.form

    # Use evaluator
    results = evaluate_full_test(questions, user_answers)

    # Store for final report
    session["test_results"] = results

    return render_template("result.html",
                           results=results,
                           role=session.get("test_role", ""),
                           level=session.get("test_level", ""),
                           user=_current_user())


# ---------------------------------------------------------------------------
# Routes — AI Interview (API-based for real-time chat)
# ---------------------------------------------------------------------------

@app.route("/interview")
def interview():
    if not _current_user():
        flash("Please login first.", "error")
        return redirect(url_for("login"))
    return render_template("interview.html", user=_current_user())


@app.route("/api/interview/start", methods=["POST"])
def api_interview_start():
    """Start a new interview session."""
    data = request.get_json() or {}
    role = data.get("role", session.get("test_role", "Software Engineer"))
    role_display = ROLE_MAP.get(role, role.replace("_", " "))
    profile = session.get("profile", {})

    interview_session = InterviewSession(role=role_display, profile=profile)
    INTERVIEW_SESSIONS[_current_user()] = interview_session

    first_question = interview_session.get_next_question()

    return jsonify({
        "status": "started",
        "question": first_question,
        "session_info": interview_session.get_status()
    })


@app.route("/api/interview/respond", methods=["POST"])
def api_interview_respond():
    """Submit an answer and get evaluation + next question."""
    user = _current_user()
    interview_session = INTERVIEW_SESSIONS.get(user)

    if not interview_session:
        return jsonify({"error": "No active interview session. Start one first."}), 400

    data = request.get_json() or {}
    answer = data.get("answer", "")

    # Evaluate the answer
    result = interview_session.submit_answer(answer)

    # Get next question
    next_q = interview_session.get_next_question()

    return jsonify({
        "evaluation": result["evaluation"],
        "has_followup": result["has_followup"],
        "next_question": next_q,
        "session_info": interview_session.get_status()
    })


@app.route("/api/interview/end", methods=["POST"])
def api_interview_end():
    """End the interview and get full evaluation."""
    user = _current_user()
    interview_session = INTERVIEW_SESSIONS.get(user)

    if not interview_session:
        return jsonify({"error": "No active interview session."}), 400

    summary = interview_session.end_session()
    session["interview_results"] = summary

    # Clean up
    del INTERVIEW_SESSIONS[user]

    return jsonify({
        "status": "completed",
        "summary": summary
    })


# ---------------------------------------------------------------------------
# Routes — Report
# ---------------------------------------------------------------------------

@app.route("/report")
def report():
    if not _current_user():
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    profile = session.get("profile")
    test_results = session.get("test_results")
    interview_results = session.get("interview_results")

    report_data = generate_report(profile, test_results, interview_results)

    return render_template("report.html",
                           report=report_data,
                           user=_current_user())


@app.route("/api/report")
def api_report():
    """JSON endpoint for the full report."""
    profile = session.get("profile")
    test_results = session.get("test_results")
    interview_results = session.get("interview_results")

    report_data = generate_report(profile, test_results, interview_results)
    return jsonify(report_data)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)