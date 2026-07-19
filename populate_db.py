from lms_main import app, db, StudentProfile, Assignment, SubmittedAssignment

with app.app_context():
    # Drop and recreate all tables (optional, fresh start)
    db.drop_all()
    db.create_all()

    # Create a student
    student = StudentProfile(
        username="Test Student",
        email="student@example.com",
        password="hashed_password",
        user_id=1
    )
    db.session.add(student)

    # Create an assignment
    assignment = Assignment(
        title="Math Assignment",
        description="Algebra"
    )
    db.session.add(assignment)

    # Commit student and assignment first
    db.session.commit()

    # Create submitted assignment
    submitted = SubmittedAssignment(
        student_id=student.id,
        assignment_id=assignment.id,
        marks_obtained=95
    )
    db.session.add(submitted)
    db.session.commit()

    print(f"{student.username} submitted {assignment.title} and got {submitted.marks_obtained} marks")
