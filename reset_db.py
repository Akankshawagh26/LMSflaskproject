import os
from lms_main import app
from models import db

with app.app_context():
    db.drop_all()
    print("🗑️ All tables dropped.")

    db.create_all()
    print("✅ New database created successfully.")