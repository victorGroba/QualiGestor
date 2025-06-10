from app import create_app, db
from app.models import Usuario, Cliente, Avaliado
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    cliente = Cliente(nome="Cliente Padrão")
    db.session.add(cliente)
    db.session.flush()

    avaliado = Avaliado(nome="Avaliado Padrão", cliente_id=cliente.id)
    db.session.add(avaliado)
    db.session.flush()

    usuario = Usuario(
        nome="Administrador",
        email="admin@admin.com",
        senha=generate_password_hash("admin123"),
        cliente_id=cliente.id,
        avaliado_id=avaliado.id,
        perfil="admin"
    )
    db.session.add(usuario)
    db.session.commit()
    print("✅ Usuário admin criado com sucesso!")
