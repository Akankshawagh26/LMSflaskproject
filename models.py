from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    student_profile = db.relationship(
        'StudentProfile',
        back_populates='user',
        uselist=False
    )



# -----------------------------
# STUDENT PROFILE
# -----------------------------


# -----------------------------
# STUDENT MARKS
class StudentMarks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    student = db.relationship('Student', backref='marks')
    subject = db.Column(db.String(50))
    marks = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# -----------------------------
# PLACEMENT UPDATE (Teacher posts jobs)
# -----------------------------

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        unique=True,
        nullable=False
    )

    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        'PlacementApplication',
        back_populates='student'
    )


class PlacementUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    package = db.Column(db.String(50))
    
    applications = db.relationship('PlacementApplication', back_populates='placement', cascade="all, delete-orphan")




class PlacementApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    placement_id = db.Column(db.Integer, db.ForeignKey('placement_update.id'), nullable=False)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='applications')
    placement = db.relationship('PlacementUpdate', back_populates='applications')


# -----------------------------
# OTHER TABLES (Assignments, Resources, Lectures, Forum)
# -----------------------------


# -----------------------------
# ASSIGNMENTS & SUBMISSIONS
# -----------------------------
# StudentProfile model
# StudentProfile
class StudentProfile(db.Model):
    __tablename__ = 'student_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', back_populates='student_profile')
    # removed submitted_assignments relationship to avoid mapper errors


class Assignment(db.Model):
    __tablename__ = 'assignment'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Text
    uploader_role = db.Column(db.String(50))
    target_role = db.Column(db.String(50), nullable=True)
    file_name = db.Column(db.String(200)) 
    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id', name='fk_assignment_uploaded_by_user'),
        nullable=True
    )
    submissions = db.relationship(
        'SubmittedAssignment',
        back_populates='assignment',
        cascade="all, delete-orphan"
    )


# change in SubmittedAssignment model
class SubmittedAssignment(db.Model):
    __tablename__ = 'submitted_assignment'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)

    marks_obtained = db.Column(db.Integer, default=0)
    submission_file = db.Column(db.String(200))

    student = db.relationship('Student', backref='submitted_assignments')
    assignment = db.relationship('Assignment', back_populates='submissions')



class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(200))
    external_link = db.Column(db.String(200))
    file_type = db.Column(db.String(50))
    uploaded_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Lecture(db.Model):
    __tablename__ = 'lecture'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ ADD THIS
    uploader = db.relationship('User', backref='lectures')

class ForumTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.String(50), nullable=False)  # Teacher / Student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    placement_id = db.Column(db.Integer, db.ForeignKey('placement_update.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    placement = db.relationship('PlacementUpdate')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref='feedbacks')

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    # password, etc.




