import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

def atualizar_banco():
    with app.app_context():
        print("--- INICIANDO ATUALIZAÇÃO DO BANCO DE DADOS ---")
        
        with db.engine.connect() as conn:
            # 1. Atualizar Tabela RESPOSTA_PERGUNTA
            print("\n>> Verificando tabela 'resposta_pergunta'...")
            
            # Adicionar status_acao
            try:
                conn.execute(text("ALTER TABLE resposta_pergunta ADD COLUMN status_acao VARCHAR(20) DEFAULT 'pendente'"))
                print("   [SUCESSO] Coluna 'status_acao' criada.")
            except Exception as e:
                print("   [INFO] Coluna 'status_acao' já existe ou erro ignorável.")

            # Adicionar acao_realizada
            try:
                conn.execute(text("ALTER TABLE resposta_pergunta ADD COLUMN acao_realizada TEXT"))
                print("   [SUCESSO] Coluna 'acao_realizada' criada.")
            except Exception as e:
                print("   [INFO] Coluna 'acao_realizada' já existe ou erro ignorável.")

            # Adicionar data_conclusao
            try:
                conn.execute(text("ALTER TABLE resposta_pergunta ADD COLUMN data_conclusao DATETIME"))
                print("   [SUCESSO] Coluna 'data_conclusao' criada.")
            except Exception as e:
                print("   [INFO] Coluna 'data_conclusao' já existe ou erro ignorável.")

            # 2. Atualizar Tabela FOTO_RESPOSTA
            print("\n>> Verificando tabela 'foto_resposta'...")
            
            # Adicionar tipo
            try:
                conn.execute(text("ALTER TABLE foto_resposta ADD COLUMN tipo VARCHAR(20) DEFAULT 'evidencia'"))
                print("   [SUCESSO] Coluna 'tipo' criada.")
            except Exception as e:
                print("   [INFO] Coluna 'tipo' já existe ou erro ignorável.")

            conn.commit()
            print("\n--- ATUALIZAÇÃO CONCLUÍDA COM SUCESSO! ---")

if __name__ == "__main__":
    atualizar_banco()