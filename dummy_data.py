from lms_main import app, db
from lms_main import User, PlacementUpdate

with app.app_context():

    print("\n--- Running Dummy Data Script ---\n")

    # 1️⃣ Teacher शोधा (role='teacher')
    teacher = User.query.filter_by(role="teacher").first()

    if not teacher:
        print("❌ No teacher found. Creating default teacher teacher1 ...")
        teacher = User(username="teacher1", password="teach123", role="teacher")
        db.session.add(teacher)
        db.session.commit()

    print(f"✔ Using Teacher: {teacher.username} (ID: {teacher.id})")

    # 2️⃣ आधीचे placements delete करा (optional पण safe)
    old = PlacementUpdate.query.filter_by(created_by=teacher.id).all()
    if old:
        print(f"🗑 Deleting {len(old)} old placements...")
        for p in old:
            db.session.delete(p)
        db.session.commit()

    # 3️⃣ नवीन placements add करा
    placement1 = PlacementUpdate(
        company="Google",
        role="Software Intern",
        package="10 LPA",
        created_by=teacher.id
    )

    placement2 = PlacementUpdate(
        company="Amazon",
        role="Data Analyst",
        package="8 LPA",
        created_by=teacher.id
    )

    db.session.add_all([placement1, placement2])
    db.session.commit()

    print("✔ Dummy placements added successfully!\n")
