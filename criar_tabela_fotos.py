from app import create_app, db
from app.models import FotoResposta

app = create_app()

with app.app_context():
    print("Conectando ao banco de dados...")
    # O create_all verifica o que falta e cria. O que já existe, ele ignora (não apaga).
    db.create_all()
    print("Banco atualizado com sucesso! Tabela 'foto_resposta' verificada/criada.")