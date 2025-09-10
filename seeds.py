# seeds.py
from app import create_app, db
from app.models import Usuario, Cliente, TipoUsuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # garante que o banco existe (útil se você pulou as migrações)
    db.create_all()

    # cria um cliente "Padrão" se não existir
    cliente = Cliente.query.filter_by(nome="Padrão").first()
    if not cliente:
        cliente = Cliente(nome="Padrão", ativo=True)
        db.session.add(cliente)
        db.session.flush()

    # cria admin se não existir
    email = "admin@admin.com"
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        user = Usuario(
            nome="Administrador",
            email=email,
            senha=generate_password_hash("admin123"),
            tipo=TipoUsuario.ADMIN if hasattr(TipoUsuario, "ADMIN") else 1,
            ativo=True,
            cliente_id=cliente.id
        )
        db.session.add(user)
        db.session.commit()
        print("✅ Usuário admin criado: admin@admin.com / admin123")
    else:
        print("ℹ️ Usuário admin já existe.")
