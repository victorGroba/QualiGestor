from app import create_app, db
from app.models import Usuario

from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    if Usuario.query.filter_by(email="admin@admin.com").first():
        print("⚠️ Usuário admin já existe.")
    else:
        admin = Usuario(
            nome="Administrador",
            email="admin@admin.com",
            senha=generate_password_hash("admin123", method="pbkdf2:sha256", salt_length=8),
            tipo="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado com sucesso!")
