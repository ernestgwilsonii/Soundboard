from app import create_app, db_orm
from app.models import AdminSettings

app = create_app()


def init_db():
    with app.app_context():
        # Models are imported via app.models which registers them with SQLAlchemy metadata
        print("Creating all database tables...")
        db_orm.create_all()

        # Ensure default settings
        AdminSettings.set_setting("featured_soundboard_id", None)
        print("Database initialized.")


if __name__ == "__main__":
    init_db()
