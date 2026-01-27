# Salve como: atualizar_banco_campos_novos.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        # Adiciona Setor
        try:
            conn.execute(text("ALTER TABLE resposta_pergunta ADD COLUMN setor_atuacao VARCHAR(100)"))
            print("Coluna 'setor_atuacao' criada.")
        except Exception as e:
            print(f"Erro/Existe 'setor_atuacao': {e}")

        # Adiciona Causa Raiz
        try:
            conn.execute(text("ALTER TABLE resposta_pergunta ADD COLUMN causa_raiz TEXT"))
            print("Coluna 'causa_raiz' criada.")
        except Exception as e:
            print(f"Erro/Existe 'causa_raiz': {e}")
            
        conn.commit()
    print("Atualização concluída!")