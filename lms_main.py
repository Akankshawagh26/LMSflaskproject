from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from sqlalchemy.orm import joinedload
from flask import send_from_directory, abort
import os
import json

# --------------------------------------
# 1) CREATE APP FIRST
# --------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lms.db"
app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --------------------------------------
# 2) INITIALIZE DB
# --------------------------------------
from models import db   # import db from models.py
db.init_app(app)



# --------------------------------------
# 4) MIGRATE — MUST COME AFTER db.init_app(app)
# --------------------------------------
from flask_migrate import Migrate
migrate = Migrate(app, db)



from models import *  
# ===================== Models =====================
from models import (
    db, User, Student, StudentMarks,
    Assignment, Resource, Lecture,
    PlacementUpdate, PlacementApplication, ForumTopic,SubmittedAssignment,Teacher
)
from utils import calculate_student_performance

# ===================== Flask Setup =====================


UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Student submissions folder
STUDENT_UPLOADS = os.path.join("static", "submissions")
os.makedirs(STUDENT_UPLOADS, exist_ok=True)

# Videos folder
VIDEOS_FOLDER = os.path.join("static", "videos")
os.makedirs(VIDEOS_FOLDER, exist_ok=True)

# Allowed video extensions
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# In-memory list to show uploaded videos (optional)
videos_list = []



# Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STUDENT_UPLOADS'] = STUDENT_UPLOADS
app.config['VIDEOS_FOLDER'] = VIDEOS_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
app.env = "development"


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===================== Login Loader =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== Helpers =====================
def allowed_file(filename):
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in {'pdf', 'docx', 'pptx', 'zip'}
    return False


# ===================== ROUTES =====================

@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"].lower()

        # Check existing username
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        # Check existing email (only for students)
        if role == "student" and Student.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create User
        new_user = User(
            username=username,
            password=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        # Create Student Profile
        if role == "student":
            student = Student(
                user_id=new_user.id,
                name=username,
                email=email,
                course="MCS"
            )

            db.session.add(student)
            db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user is None:
            flash("Username not found!", "danger")
            return redirect(url_for("login"))

        if not check_password_hash(user.password, password):
            flash("Incorrect password!", "danger")
            return redirect(url_for("login"))

        login_user(user)

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        if user.role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif user.role == "student":
            return redirect(url_for("student_dashboard"))

        flash("Invalid role!", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/auto-login/<int:user_id>')
def auto_login(user_id):
    user = User.query.get(user_id)
    if user:
        login_user(user)
        return redirect(url_for('student_dashboard'))  # student_dashboard ही तुमच्या route ची function name असावी
    return "User not found", 404

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/uploads/<filename>")
def serve_uploads(filename):
    if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return send_from_directory(UPLOAD_FOLDER, filename)
    else:
        abort(404)

@app.route("/assignments/<filename>")
def serve_assignments(filename):
    if os.path.exists(os.path.join("static/assignments", filename)):
        return send_from_directory("static/assignments", filename)
    else:
        abort(404)
# =======================================
# TEACHER ROUTES
# =======================================
@app.route("/teacher/dashboard")
def teacher_dashboard():

    if session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Teacher logged in as USER
    user = User.query.get(session["user_id"])

    # 🔹 Assignments uploaded by this user
    total_assignments = Assignment.query.filter_by(
        uploaded_by=user.id
    ).count()

    # 🔹 Student submissions on teacher assignments
    submitted_assignments = SubmittedAssignment.query.join(Assignment).filter(
        Assignment.uploaded_by == user.id
    ).count()

    # 🔹 Completion rate
    completion_rate = (
        int((submitted_assignments / total_assignments) * 100)
        if total_assignments else 0
    )

    # 🔹 Latest lectures (GLOBAL – avoids Teacher/User mismatch)
    latest_lectures = Lecture.query.order_by(
        Lecture.created_at.desc()
    ).limit(3).all()

    return render_template(
        "teacher/dashboard.html",
        user=user,
        total_assignments=total_assignments,
        submitted_assignments=submitted_assignments,
        completion_rate=completion_rate,
        latest_lectures=latest_lectures
    )


# 📌 Teacher: Upload Assignment
# ===============================
# Teacher upload assignment
@app.route("/teacher/upload-assignment", methods=["GET", "POST"])
def teacher_upload_assignment():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        file = request.files.get("file")

        if not title or not file or file.filename == '':
            flash("Please provide title and file!", "warning")
            return redirect(url_for("teacher_upload_assignment"))

        filename = secure_filename(file.filename)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        new_assignment = Assignment(
            title=title,
            file_name=filename,
            uploaded_by=session.get("user_id"),
            uploader_role="teacher",
            target_role="student"
        )
        db.session.add(new_assignment)
        db.session.commit()
        flash("Assignment uploaded successfully!", "success")
        return redirect(url_for("teacher_assignments"))

    return render_template("teacher/upload_assignment.html")


# Teacher view all uploaded assignments
@app.route("/teacher/assignments")
def teacher_assignments():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    assignments = Assignment.query.filter_by(uploader_role="teacher").all()
    return render_template("teacher/assignments.html", assignments=assignments)

# ===============================
# 📌 Teacher: View Student Submissions
# ===============================
# ==========================
# Teacher: View & Assign Marks
# ==========================
@app.route('/teacher/submissions/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def teacher_submissions(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = SubmittedAssignment.query.filter_by(assignment_id=assignment.id).all()

    if request.method == 'POST':
        for sub in submissions:
            mark = request.form.get(f'mark_{sub.id}')
            if mark and sub.student:  # only update if student exists
                sub.marks_obtained = int(mark)
        db.session.commit()
        flash("Marks updated successfully!", "success")
        return redirect(url_for('teacher_submissions', assignment_id=assignment_id))

    return render_template('teacher/submissions.html', assignment=assignment, submissions=submissions)




# ===============================
# 🗑 Teacher: Delete Assignment
# ===============================
@app.route("/teacher/delete_assignment/<int:id>", methods=["POST"])
def delete_assignment(id):
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    assignment = Assignment.query.get_or_404(id)

    file_path = os.path.join("static", "assignments", assignment.file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(assignment)
    db.session.commit()

    flash("🗑 Assignment deleted!", "success")
    return redirect(url_for("teacher_assignments"))


# ===============================
# 📌 Serve Uploaded Files
# ===============================
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/assignments/<filename>")
def serve_uploaded_file(filename):
    return send_from_directory("static/assignments", filename)

@app.route("/teacher/videos", methods=['GET', 'POST'])
@login_required
def teacher_videos():
    if request.method == "POST":
        title = request.form["title"]
        file = request.files["video"]

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['VIDEOS_FOLDER'], filename))

            new_video = Lecture(title=title, filename=filename, uploader_id=current_user.id)
            db.session.add(new_video)
            db.session.commit()

            flash("Video uploaded successfully!", "success")
            return redirect(url_for("teacher_videos"))

    # Fetch all teacher videos
    videos = Lecture.query.order_by(Lecture.created_at.desc()).all()
    return render_template("teacher/videos.html", videos=videos)


@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['VIDEOS_FOLDER'], filename)


# ---------- TEACHER FORUM ----------
# Teacher Forum List + Add
@app.route('/teacher/forum', methods=['GET', 'POST'])
def teacher_forum():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        posted_by = "Teacher"

        new_topic = ForumTopic(title=title, description=description, posted_by=posted_by)
        db.session.add(new_topic)
        db.session.commit()
        return redirect(url_for('teacher_forum'))

    topics = ForumTopic.query.order_by(ForumTopic.created_at.desc()).all()
    
    return render_template("teacher/forum_topic.html", topics=topics)


# View Topic
@app.route('/teacher/forum/view/<int:topic_id>')
def teacher_view_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    return render_template('teacher/forum_view.html', topic=topic)


# Delete Topic
@app.route('/teacher/forum/delete/<int:topic_id>', methods=['POST'])
def teacher_delete_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash("Topic deleted successfully!", "success")
    return redirect(url_for('teacher_forum'))

@app.route('/teacher/student_performance', endpoint='teacher_student_performance')
def student_performance():

    students = Student.query.all()
    assignments = Assignment.query.all()
    performance_data = []

    for student in students:
        student_data = {
            'name': student.name,
            'marks': [],
            'total_obtained': 0,
            'total_marks': 0
        }
        for assignment in assignments:
            submission = SubmittedAssignment.query.filter_by(
                student_id=student.id,
                assignment_id=assignment.id
            ).first()
            obtained = submission.obtained_marks if submission else 0
            student_data['marks'].append({
                'assignment': assignment.title,
                'obtained': obtained,
                'total': assignment.total_marks
            })
            student_data['total_obtained'] += obtained
            student_data['total_marks'] += assignment.total_marks

        student_data['percentage'] = round(
            (student_data['total_obtained'] / student_data['total_marks']) * 100, 2
        ) if student_data['total_marks'] > 0 else 0

        performance_data.append(student_data)

    return render_template(
        'teacher/performance.html',
        performance_data=performance_data,
        assignments=assignments
    )


@app.route("/teacher/resources", methods=["GET", "POST"])
def teacher_resources():
    if request.method == "POST":
        title = request.form.get("title")
        link = request.form.get("link")
        file = request.files.get("file")

        if not title:
            flash("Title is required!", "danger")
            return redirect(url_for("teacher_resources"))

        filename = None
        file_type = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(app.static_folder, "uploads"), exist_ok=True)
            file.save(os.path.join(app.static_folder, "uploads", filename))
            file_type = filename.rsplit(".", 1)[1].lower()
        elif link:
            file_type = "link"

        new_res = Resource(
            title=title,
            file_url=filename,
            external_link=link,
            file_type=file_type,
            uploaded_by="Teacher"
        )
        db.session.add(new_res)
        db.session.commit()
        flash("Resource uploaded successfully!", "success")
        return redirect(url_for("teacher_resources"))

    resources = Resource.query.all()
    return render_template("teacher/resources.html", resources=resources)


# Edit resource title
@app.route("/teacher/resources/edit/<int:res_id>", methods=["POST"])
def edit_resource(res_id):
    resource = Resource.query.get_or_404(res_id)
    new_title = request.form.get("title")
    if new_title:
        resource.title = new_title
        db.session.commit()
        flash("Resource updated successfully!", "success")
    else:
        flash("Title cannot be empty!", "danger")
    return redirect(url_for("teacher_resources"))


# Delete resource
@app.route("/teacher/resources/delete/<int:res_id>")
def delete_resource(res_id):
    resource = Resource.query.get_or_404(res_id)
    # Delete uploaded file from server
    if resource.file_url:
        file_path = os.path.join(app.static_folder, "uploads", resource.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(resource)
    db.session.commit()
    flash("Resource deleted successfully!", "success")
    return redirect(url_for("teacher_resources"))


# Teacher placement list
@app.route('/teacher/placement/add', methods=['GET', 'POST'])
@login_required
def teacher_add_placement():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    if request.method == "POST":
        company = request.form['company']
        role = request.form['role']
        package = request.form['package']
        db.session.add(PlacementUpdate(company=company, role=role, package=package))
        db.session.commit()
        flash("Placement added!", "success")
        return redirect(url_for('teacher_placement_list'))
    return render_template("teacher/placement_add.html")


@app.route('/teacher/placement/list')
@login_required
def teacher_placement_list():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    placements = PlacementUpdate.query.all()
    return render_template("teacher/placement_list.html", placements=placements)




@app.route('/teacher/placement/delete/<int:placement_id>', methods=['POST'])
@login_required
def teacher_delete_placement(placement_id):
    placement = PlacementUpdate.query.get_or_404(placement_id)
    db.session.delete(placement)
    db.session.commit()
    flash("Placement deleted successfully!", "success")
    return redirect(url_for('teacher_placement_list'))





@app.route('/teacher/placement/edit/<int:placement_id>', methods=['GET','POST'])
@login_required
def teacher_edit_placement(placement_id):
    placement = PlacementUpdate.query.get_or_404(placement_id)
    if request.method == 'POST':
        placement.company = request.form.get('company')
        placement.role = request.form.get('role')
        placement.package = request.form.get('package')
        db.session.commit()
        flash("Placement updated successfully!", "success")
        return redirect(url_for('teacher_placement_list'))
    return render_template("teacher/edit_placement.html", placement=placement)




# ------------------------------
# STUDENT : VIEW AVAILABLE PLACEMENTS
# ------------------------------

@app.route('/teacher/feedbacks')
@login_required
def teacher_view_feedbacks():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('teacher/feedback_list.html', feedbacks=feedbacks)




@app.route('/teacher/feedback/chart-data')
@login_required
def feedback_chart_data():
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403

    # Aggregate ratings
    from sqlalchemy import func
    data = db.session.query(
        Feedback.rating,
        func.count(Feedback.id)
    ).group_by(Feedback.rating).all()

    chart_data = {str(rating): count for rating, count in data}
    return jsonify(chart_data)




@app.route('/teacher/upload', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['video']

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            lecture = Lecture(title=title, filename=filename, uploader_id=current_user.id)
            db.session.add(lecture)
            db.session.commit()

            return "Video Uploaded Successfully!"

    return render_template("upload_video.html")

# -----------------------------
# TEACHER → ADD STUDENT
# -----------------------------

@app.route("/student/dashboard")
@login_required
def student_dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        flash("Student profile not found. Contact admin.", "danger")
        return redirect(url_for("logout"))

    total_assignments = Assignment.query.count()
    submitted_assignments = SubmittedAssignment.query.filter_by(
        student_id=student.id
    ).count()

    completion_rate = (
        (submitted_assignments / total_assignments) * 100
        if total_assignments else 0
    )

    return render_template(
        "student/dashboard.html",
        student=student,
        total_assignments=total_assignments,
        submitted_assignments=submitted_assignments,
        completion_rate=completion_rate
    )


@app.route("/teacher/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]
        default_password = "12345"

        # 🔴 CHECK 1: Student already exists (IMPORTANT)
        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            flash("Student already exists!", "danger")
            return redirect(url_for("add_student"))

        # 🔴 CHECK 2: User already exists
        existing_user = User.query.filter_by(username=email).first()
        if existing_user:
            flash("User already exists!", "danger")
            return redirect(url_for("add_student"))

        # Create User
        hashed_password = generate_password_hash(default_password)
        new_user = User(
            username=email,
            password=hashed_password,
            role="student"
        )
        db.session.add(new_user)
        db.session.commit()

        # Create Student
        new_student = Student(
            name=name,
            email=email,
            course=course,
            user_id=new_user.id
        )
        db.session.add(new_student)
        db.session.commit()

        flash("Student added successfully!", "success")
        return redirect(url_for("student_list"))

    return render_template("teacher/add_student.html")



# ========================================
# ===================== Student Routes =====================

# Student view teacher assignments
@app.route("/student/assignments")
def student_assignments():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    teacher_assignments = Assignment.query.filter_by(
        uploader_role="teacher",
        target_role="student"
    ).all()

    return render_template(
        "student/assignments.html",
        assignments=teacher_assignments  # ✅ must pass variable
    )


# Student upload / submit assignment
@app.route("/student/upload-assignment/<int:assignment_id>", methods=["GET", "POST"])
@login_required
def student_upload_assignment(assignment_id):
    if session.get("role") != "student":
        return redirect(url_for("login"))

    assignment = Assignment.query.get_or_404(assignment_id)

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student profile not found!", "danger")
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        file = request.files.get("file")
        if not file or not allowed_file(file.filename):
            flash("Please upload valid file!", "warning")
            return redirect(url_for("student_upload_assignment", assignment_id=assignment_id))

        filename = secure_filename(file.filename)
        os.makedirs(app.config["STUDENT_UPLOADS"], exist_ok=True)
        file.save(os.path.join(app.config["STUDENT_UPLOADS"], filename))

        submission = SubmittedAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            submission_file=filename
        )
        db.session.add(submission)
        db.session.commit()

        flash("Assignment submitted successfully!", "success")
        return redirect(url_for("student_assignments"))

    return render_template("student/upload_assignment.html", assignment=assignment)


# Student submitted files
@app.route("/submissions/<filename>")
def serve_student_submission(filename):
    return send_from_directory(app.config["STUDENT_UPLOADS"], filename)




# ---------- EXTRA STUDENT PAGES ----------
@app.route("/student/resources")
def student_resources():
    resources = Resource.query.all()
    return render_template("student/resources.html", resources=resources)

@app.route("/student/videos")
@login_required
def student_videos():
    lectures = Lecture.query.order_by(Lecture.created_at.desc()).all()
    return render_template("student/videos.html", lectures=lectures)





# Student: View Placements
# -------------------------------
@app.route('/student/placements')
@login_required
def student_view_placements():
    placements = PlacementUpdate.query.all()

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student profile not found!", "danger")
        return redirect(url_for("student_dashboard"))

    applied_ids = [app.placement_id for app in student.applications]

    return render_template(
        'student/placement_view.html',
        placements=placements,
        applied_ids=applied_ids
    )

# -----------------------------
# Apply Placement
# -----------------------------
@app.route('/student/apply/<int:placement_id>', methods=['POST'])
@login_required
def student_apply_placement(placement_id):
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student profile not found!", "danger")
        return redirect(url_for("student_dashboard"))

    existing = PlacementApplication.query.filter_by(
        student_id=student.id,
        placement_id=placement_id
    ).first()

    if existing:
        flash("You have already applied.", "warning")
        return redirect(url_for('student_view_placements'))

    application = PlacementApplication(
        student_id=student.id,
        placement_id=placement_id,
        date_applied=datetime.utcnow()
    )
    db.session.add(application)
    db.session.commit()

    flash("Applied Successfully!", "success")
    return redirect(url_for('student_view_placements'))

# ------------------------------------
# STUDENT FORUM (LIST + ADD)
# ------------------------------------
@app.route('/student/forum', methods=['GET', 'POST'])
def student_forum():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        posted_by = "Student"

        new_topic = ForumTopic(
            title=title,
            description=description,
            posted_by=posted_by
        )
        db.session.add(new_topic)
        db.session.commit()

        return redirect(url_for('student_forum'))

    topics = ForumTopic.query.order_by(ForumTopic.created_at.desc()).all()
    return render_template("student/forum.html", topics=topics)


# ------------------------------------
# VIEW + EDIT TOPIC
# ------------------------------------
# VIEW + EDIT TOPIC
@app.route('/student/forum/topic/<int:topic_id>', methods=['GET', 'POST'])
def student_forum_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)

    if request.method == 'POST':
        topic.title = request.form['title']
        topic.description = request.form['description']
        db.session.commit()
        flash("Topic updated successfully!", "success")
        return redirect(url_for('student_forum_topic', topic_id=topic.id))

    return render_template("student/forum_topic.html", topic=topic)


# DELETE TOPIC
@app.route('/student/forum/topic/delete/<int:topic_id>', methods=['POST'])
def delete_student_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash("Topic deleted successfully!", "success")
    return redirect(url_for('student_forum'))


@app.route("/student/profile")
def student_profile():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        flash("Student profile not found!", "danger")
        return redirect(url_for("student_dashboard"))

    return render_template("student/profile.html", role="student", student=student)



# Student Feedback Form
@app.route('/student/feedback', methods=['GET', 'POST'])
@login_required
def student_feedback():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Complete your profile first!", "warning")
        return redirect(url_for("student_dashboard"))

    if request.method == 'POST':
        subject = request.form['subject']
        rating = int(request.form['rating'])
        comments = request.form['comments']

        new_feedback = Feedback(
            student_id=student.id,
            subject=subject,
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback submitted successfully!", "success")
        return redirect(url_for('student_feedback'))

    return render_template('student/feedback.html')

# =======================================
# FILE DOWNLOAD
# =======================================


@app.route("/teacher/students")
def student_list():
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template("teacher/student_list.html", students=students)

# =======================================
# MAIN
# =======================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
