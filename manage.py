from flask_migrate import Migrate
from lms_main import app, db  # तुमच्या main file मधून import करा

migrate = Migrate(app, db)

# Optional: Flask CLI shell context
from flask.cli import FlaskGroup
cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()
