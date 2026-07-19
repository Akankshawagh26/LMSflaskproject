from lms_main import app, db
from models import User, Student

with app.app_context():
    for u in User.query.all():
        new_s = Student(
            name=u.username,
            email=u.username,
            user_id=u.id
        )
        db.session.add(new_s)

    db.session.commit()
    print("All students created!")
