# atualizar_banco_fluxograma.py
import sys
import os
from sqlalchemy import text, inspect

# Adiciona o diretório atual ao path para encontrar o 'app'
sys.path.append(os.getcwd())

from app import create_app, db

app = create_app()

def migrar_banco():
    with app.app_context():
        print("--- Iniciando Migração Segura (v2): Fluxograma ---")
        
        engine = db.engine
        print(f"Banco conectado: {engine.url}")
        
        # 1. Usar o Inspector para ler as colunas sem gerar erro SQL
        inspector = inspect(engine)
        colunas = [col['name'] for col in inspector.get_columns('aplicacao_questionario')]
        
        if 'fluxograma_arquivo' in colunas:
            print("⚠️  A coluna 'fluxograma_arquivo' JÁ EXISTE no banco. Nenhuma alteração necessária.")
        else:
            print("Coluna não encontrada. Criando agora...")
            
            # 2. Abre uma conexão nova e limpa para executar a alteração
            with engine.connect() as conn:
                # O 'with conn.begin()' garante commit automático ou rollback em caso de erro
                with conn.begin():
                    sql_add = text("ALTER TABLE aplicacao_questionario ADD COLUMN fluxograma_arquivo VARCHAR(255)")
                    conn.execute(sql_add)
            
            print("✅ Coluna 'fluxograma_arquivo' criada com sucesso!")

        print("--- Migração Finalizada ---")

if __name__ == "__main__":
    migrar_banco()