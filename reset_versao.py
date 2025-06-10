from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.session.execute(text('DROP TABLE IF EXISTS alembic_version'))
    db.session.commit()
    print("Tabela alembic_version removida com sucesso.")
