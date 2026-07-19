from models import StudentMarks, Student

def calculate_student_performance(student_id):
    marks_list = StudentMarks.query.filter_by(student_id=student_id).all()
    if not marks_list:
        return 0
    total_marks = sum(m.marks for m in marks_list)
    average = total_marks / len(marks_list)
    return round(average, 2)

def calculate_teacher_performance(teacher_id):
    # teacher subjects साठी सर्व student marks fetch करा
    students_marks = StudentMarks.query.join(Student).filter(Student.teacher_id==teacher_id).all()
    if not students_marks:
        return 0
    total_marks = sum(m.marks for m in students_marks)
    average = total_marks / len(students_marks)
    return round(average, 2)
