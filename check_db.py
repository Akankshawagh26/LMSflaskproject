# from lms_app import app, db, User, Assignment

# with app.app_context():
#     print("✅ Tables:", db.metadata.tables.keys())

#     users = User.query.all()
#     assignments = Assignment.query.all()

#     print("\n👤 Users:")
#     for u in users:
#         print(u.id, u.username, u.password, u.role)

#     print("\n🧾 Assignments:")
#     for a in assignments:
#         print(a.id, a.filename, a.date_uploaded, a.status)
# from lms_app import db
# print(db.metadata.tables.keys())
